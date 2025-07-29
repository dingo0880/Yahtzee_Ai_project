import random
from collections import Counter
import pandas as pd
import time
import os
import sys
import itertools

# --- 기본 설정 및 AI 핵심 로직 ---
CATEGORIES = [
    "Ones", "Twos", "Threes", "Fours", "Fives", "Sixes",
    "Four of a Kind", "Full House",
    "Small Straight", "Large Straight", "Yahtzee", "Chance"
]
CPU_TYPES = ["엘리트형", "공격형", "안정형", "일반형"]

BASE_WEIGHTS = {
    "Ones": 0.3, "Twos": 0.4, "Threes": 0.6, "Fours": 0.8, "Fives": 1.0, "Sixes": 1.2,
    "Four of a Kind": 1.8, "Full House": 2.0, "Small Straight": 1.1, "Large Straight": 1.6,
    "Yahtzee": 3.0, "Chance": 1.0
}

# --- AI 핵심 두뇌: 몬테카를로 시뮬레이션 (결함 포함) ---
def estimate_expected_score(dice, keep_idxs, scoreboard, turn, n_sim=500):
    """
    [v1.0의 핵심] keep_idxs만 고정하고, 나머지를 재굴림했을 때의
    기대 점수를 Monte Carlo 방식으로 계산합니다.
    
    [치명적 결함] 이 함수는 남은 굴림 횟수와 상관없이
    항상 '2번' 더 굴릴 수 있다고 착각하여 미래를 예측합니다.
    """
    total = 0
    w = dynamic_weights(turn, scoreboard)
    for _ in range(n_sim):
        sim = dice.copy()
        # ▼▼▼ 여기가 바로 '결함'이 있는 부분 ▼▼▼
        for _ in range(2): # 항상 2번 굴린다고 가정
            for i in range(5):
                if i not in keep_idxs:
                    sim[i] = random.randint(1,6)
        # ▲▲▲ 여기가 바로 '결함'이 있는 부분 ▲▲▲
        
        best_cat = max(
            (c for c,s in scoreboard.items() if s is None),
            key=lambda c: score_category(sim, c) * w.get(c,1.0),
            default="Chance"
        )
        total += score_category(sim, best_cat)
    return total / n_sim

# --- 점수 계산 및 기타 함수 ---
def score_category(dice, category):
    counts = Counter(dice)
    dice_set = set(dice)
    if category == "Ones": return dice.count(1)
    if category == "Twos": return dice.count(2) * 2
    if category == "Threes": return dice.count(3) * 3
    if category == "Fours": return dice.count(4) * 4
    if category == "Fives": return dice.count(5) * 5
    if category == "Sixes": return dice.count(6) * 6
    if category == "Four of a Kind": return sum(dice) if max(counts.values()) >= 4 else 0
    if category == "Full House": return 25 if sorted(counts.values()) == [2,3] else 0
    if category == "Small Straight":
        for seq in ([1,2,3,4],[2,3,4,5],[3,4,5,6]):
            if set(seq).issubset(dice_set): return 15
        return 0
    if category == "Large Straight":
        return 30 if sorted(set(dice)) in ([1,2,3,4,5],[2,3,4,5,6]) else 0
    if category == "Yahtzee": return 50 if max(counts.values()) == 5 else 0
    if category == "Chance": return sum(dice)
    return 0

def calculate_upper_score(scoreboard):
    return sum(score for cat, score in scoreboard.items() if cat in CATEGORIES[:6] and score is not None)

def calculate_bonus(upper_score):
    return 35 if upper_score >= 63 else 0

def dynamic_weights(turn, scoreboard):
    w = BASE_WEIGHTS.copy()
    upper_done = calculate_upper_score(scoreboard) >= 63
    if turn <= 7 and not upper_done:
        for cat in CATEGORIES[:6]:
            w[cat] *= 1.5
    if turn >= 8 or upper_done:
        for cat in ("Yahtzee","Full House"):
            w[cat] *= 1.5
    return w

def get_recommended_target(dice, scoreboard, turn):
    w = dynamic_weights(turn, scoreboard)
    possible = [c for c,s in scoreboard.items() if s is None]
    if not possible: return "Chance"
    return max(possible, key=lambda c: score_category(dice,c) * w.get(c,1.0))

# --- 각 CPU 유형별 전략 함수 ---
def strategic_keep_elite(dice, scoreboard, turn):
    """
    후보집합(모든 부분집합 + 휴리스틱)에 대해
    결함이 있는 몬테카를로 시뮬레이션을 실행하여 최적의 수를 찾습니다.
    """
    counts = Counter(dice)
    candidates = [list(c) for r in range(6) for c in itertools.combinations(range(5), r)]

    if counts:
        top = counts.most_common(1)[0][0]
        candidates += [
            [],
            list(range(5)),
            [i for i,d in enumerate(dice) if d==top],
        ]
    
    rec = get_recommended_target(dice, scoreboard, turn)
    if rec in CATEGORIES[:6]:
        face = CATEGORIES.index(rec)+1
        candidates.append([i for i,d in enumerate(dice) if d==face])

    unique_cands = []
    for c in candidates:
        if c not in unique_cands:
            unique_cands.append(c)

    best_keep, best_ev = [], -1
    for keep in unique_cands:
        ev = estimate_expected_score(dice, keep, scoreboard, turn, n_sim=500)
        if ev > best_ev:
            best_ev, best_keep = ev, keep
    return best_keep

def strategic_keep_attack(dice, scoreboard, turn):
    counts = Counter(dice)
    if scoreboard.get("Yahtzee") is None and counts.most_common(1) and counts.most_common(1)[0][1] >= 3:
        return [i for i,d in enumerate(dice) if d==counts.most_common(1)[0][0]]
    if scoreboard.get("Full House") is None and sorted(counts.values())==[2,3]:
        return list(range(5))
    rec = get_recommended_target(dice, scoreboard, turn)
    if rec in CATEGORIES[:6]:
        return [i for i,d in enumerate(dice) if d==CATEGORIES.index(rec)+1]
    if counts: return [i for i,d in enumerate(dice) if d==counts.most_common(1)[0][0]]
    return []

def strategic_keep_defense(dice, scoreboard, turn):
    counts = Counter(dice)
    upper_score = calculate_upper_score(scoreboard)
    remain_upper = [c for c in CATEGORIES[:6] if scoreboard[c] is None]
    if upper_score < 63 and remain_upper:
        rec = max(remain_upper, key=lambda c: score_category(dice,c))
        face = CATEGORIES.index(rec)+1
        return [i for i,d in enumerate(dice) if d==face]
    possible = [c for c, s in scoreboard.items() if s is None]
    if not possible: return list(range(5))
    rec = max(possible, key=lambda c: score_category(dice,c))
    if rec in CATEGORIES[:6]:
        return [i for i,d in enumerate(dice) if d==CATEGORIES.index(rec)+1]
    if counts: return [i for i,d in enumerate(dice) if d==counts.most_common(1)[0][0]]
    return []

def strategic_keep_normal(dice, scoreboard, turn):
    counts = Counter(dice)
    patterns = {"Small Straight":[[1,2,3,4],[2,3,4,5],[3,4,5,6]], "Large Straight":[[1,2,3,4,5],[2,3,4,5,6]]}
    for cat,pats in patterns.items():
        if scoreboard.get(cat) is None:
            for pat in pats:
                if set(pat).issubset(set(dice)): return [i for i,d in enumerate(dice) if d in pat]
    rec = get_recommended_target(dice, scoreboard, turn)
    if rec in CATEGORIES[:6]:
        return [i for i,d in enumerate(dice) if d==CATEGORIES.index(rec)+1]
    if counts: return [i for i,d in enumerate(dice) if d==counts.most_common(1)[0][0]]
    return []

def strategic_decide_dice_to_keep(dice, scoreboard, turn, cpu_type):
    if cpu_type == "엘리트형": return strategic_keep_elite(dice, scoreboard, turn)
    if cpu_type == "공격형": return strategic_keep_attack(dice, scoreboard, turn)
    if cpu_type == "안정형": return strategic_keep_defense(dice, scoreboard, turn)
    return strategic_keep_normal(dice, scoreboard,turn)

def cpu_select_category(dice, scoreboard, cpu_type, turn):
    if cpu_type == "엘리트형":
        w = dynamic_weights(turn, scoreboard)
        possible = [c for c,s in scoreboard.items() if s is None]
        if not possible: return "Chance"
        return max(possible, key=lambda c: score_category(dice, c) * w.get(c,1.0))
    
    possible = [c for c,s in scoreboard.items() if s is None]
    if not possible: return "Chance"
    max_scores = {
        "Ones":5, "Twos":10, "Threes":15, "Fours":20, "Fives":25, "Sixes":30,
        "Four of a Kind":sum(dice), "Full House":25, "Small Straight":15, "Large Straight":30,
        "Yahtzee":50, "Chance":sum(dice)
    }
    regrets = [(c, max_scores[c] - score_category(dice,c)) for c in possible]
    return min(regrets, key=lambda x: x[1])[0]

# --- UI 및 게임 흐름 함수 ---
def display_scoreboard(player_name, scoreboard):
    print(f"\n--- {player_name}의 점수판 ---")
    upper_score = calculate_upper_score(scoreboard)
    bonus = calculate_bonus(upper_score)
    total_score = sum(v for v in scoreboard.values() if v is not None) + bonus
    for idx, cat in enumerate(CATEGORIES, 1):
        val = scoreboard.get(cat)
        print(f"{idx:2}. {cat:<15}: {val if val is not None else '-'}")
    print("-------------------------")
    print(f"상단 합계: {upper_score} / 63  (보너스: +{bonus})")
    print(f"총합: {total_score}")
    print("=========================")

def display_dice_with_indices(dice):
    print("\n현재 주사위:")
    for i, d in enumerate(dice, 1):
        print(f"  {i}: 🎲 {d}")

def play_turn(player, turn_num, player_logs):
    scoreboard = player['scoreboard']
    player_name, is_cpu, cpu_type = player['name'], player['is_cpu'], player['type']
    print(f"\n<<<<< {player_name}의 {turn_num}턴 >>>>>")
    dice = [random.randint(1, 6) for _ in range(5)]
    log = []
    
    roll_number = 0
    for r in range(1, 4):
        roll_number = r
        if not is_cpu:
            display_scoreboard(player_name, scoreboard)
        display_dice_with_indices(dice)
        if not is_cpu:
            log.append(f"🎲 {r}차 굴림: {dice}")
        if r == 3:
            break
        
        if is_cpu:
            keep = strategic_decide_dice_to_keep(dice, scoreboard, r, cpu_type)
            if len(keep) == 5:
                print("CPU: 모든 주사위 고정.")
                break
            print(f"CPU ({cpu_type}) 고정: {[dice[i] for i in keep]}")
            time.sleep(1)
            new_dice = [d for i, d in enumerate(dice) if i in keep]
            new_dice.extend([random.randint(1, 6) for _ in range(5 - len(new_dice))])
            dice = new_dice
        else:
            raw = input("재굴림할 주사위 번호 (예:13, 엔터 시 중단): ").strip()
            if not raw:
                log.append(f"{r}차 굴림 종료 (엔터 입력)")
                break
            reroll_indices = {int(c) - 1 for c in raw if c.isdigit() and 1 <= int(c) <= 5}
            log.append(f"{r}차 굴림 - 재굴림: {sorted([i+1 for i in reroll_indices])}")
            for idx in reroll_indices:
                dice[idx] = random.randint(1, 6)

    if is_cpu:
        display_scoreboard(player_name, scoreboard)
        choice = cpu_select_category(dice, scoreboard, cpu_type, turn_num)
    else:
        while True:
            display_scoreboard(player_name, scoreboard)
            possible = {c: score_category(dice, c) for c, s in scoreboard.items() if s is None}
            print("--- 기록할 족보 선택 ---")
            for i, (cat, sc) in enumerate(possible.items(), 1):
                print(f"{i}. {cat} ({sc}점)")
            
            if roll_number < 3:
                print("0. 다시 주사위 굴리기")
            
            sel = input(f"번호 선택 (0-{len(possible)}): ").strip()

            if sel == '0' and roll_number < 3:
                print("\n🔄 남은 굴림을 계속 진행합니다.")
                for r_cont in range(roll_number + 1, 4):
                    roll_number = r_cont
                    display_dice_with_indices(dice)
                    raw = input("재굴림할 주사위 번호 (예:13, 엔터 시 중단): ").strip()
                    if not raw:
                        log.append(f"{r_cont}차 굴림 전 중단")
                        break
                    reroll_indices = {int(c) - 1 for c in raw if c.isdigit() and 1 <= int(c) <= 5}
                    log.append(f"{r_cont}차 굴림 - 재굴림: {sorted([i+1 for i in reroll_indices])}")
                    for idx in reroll_indices:
                        dice[idx] = random.randint(1, 6)
                continue
            elif sel.isdigit() and 1 <= int(sel) <= len(possible):
                choice = list(possible.keys())[int(sel) - 1]
                break
            else:
                print("잘못된 입력입니다. 다시 선택해주세요.")

    score = score_category(dice, choice)
    scoreboard[choice] = score
    log.append(f"최종 선택: {choice} ({score}점)")
    if not is_cpu:
        player_logs.setdefault(player_name, []).extend([f"[{turn_num}턴]"] + log)
    print(f"-> {player_name}님이 '{choice}'에 {score}점을 기록했습니다.")
    time.sleep(1)

def print_final_scores(players):
    print("\n\n#####################\n##### 최종 결과 #####\n#####################")
    final_scores = []
    for p in players:
        upper_score = calculate_upper_score(p["scoreboard"])
        bonus = calculate_bonus(upper_score)
        total_score = sum(v for v in p["scoreboard"].values() if v is not None) + bonus
        final_scores.append({"name": p["name"], "score": total_score})
    final_scores.sort(key=lambda x: x["score"], reverse=True)
    for i, result in enumerate(final_scores):
        print(f"{i + 1}위: {result['name']} - {result['score']}점")
    if len(final_scores) > 1:
        print(f"\n🏆 최종 우승자: {final_scores[0]['name']} ({final_scores[0]['score']}점)")

# --- 시뮬레이션 함수 ---
def run_single_game_simulation(cpu_type):
    scoreboard = {c: None for c in CATEGORIES}
    for turn in range(1, 13):
        dice = [random.randint(1, 6) for _ in range(5)]
        for r in range(2):
            keep = strategic_decide_dice_to_keep(dice, scoreboard, turn, cpu_type)
            if len(keep) == 5: break
            new_dice = [d for i, d in enumerate(dice) if i in keep]
            new_dice.extend([random.randint(1, 6) for _ in range(5 - len(new_dice))])
            dice = new_dice
        
        choice = cpu_select_category(dice, scoreboard, cpu_type, turn)
        if scoreboard.get(choice) is None:
            scoreboard[choice] = score_category(dice, choice)
        else:
            possible = [c for c, s in scoreboard.items() if s is None]
            if possible:
                scoreboard[possible[0]] = score_category(dice, possible[0])
    
    upper_score = calculate_upper_score(scoreboard)
    bonus = calculate_bonus(upper_score)
    total_score = sum(v for v in scoreboard.values() if v is not None) + bonus
    return total_score

def analyze_cpu_performance(cpu_type, num_simulations=100):
    print(f"\n===== CPU 유형: [{cpu_type}] 성능 분석 =====")
    print(f"시뮬레이션 횟수: {num_simulations}회")
    print("분석 중...")
    scores = [run_single_game_simulation(cpu_type) for _ in range(num_simulations)]
    scores_series = pd.Series(scores)
    print("\n--- 📊 통계 결과 ---")
    print(f"평균 점수  : {scores_series.mean():.2f}점")
    print(f"중앙값      : {scores_series.median():.2f}점")
    print(f"표준 편차  : {scores_series.std():.2f}")
    print(f"최고 점수  : {scores_series.max()}점")
    print(f"최저 점수  : {scores_series.min()}점")
    mode_values = scores_series.mode()
    if not mode_values.empty:
        print(f"최빈값      : {', '.join(map(str, mode_values.values))}점")
    else:
        print("최빈값      : 없음")
    print("--------------------")

def save_all_logs(player_logs):
    try:
        base_dir = os.path.dirname(sys.executable if getattr(sys, 'frozen', False) else os.path.abspath(__file__))
    except NameError:
        base_dir = "."
    for name, logs in player_logs.items():
        base_filename = f"log_{name}.txt"
        filename = os.path.join(base_dir, base_filename)
        count = 1
        while os.path.exists(filename):
            filename = os.path.join(base_dir, f"log_{name}({count}).txt")
            count += 1
        with open(filename, "w", encoding="utf-8") as f:
            for line in logs:
                f.write(line + "\n")
        print(f"📁 로그 저장 완료: {os.path.basename(filename)}")

# --- 메인 실행 ---
if __name__ == '__main__':
    while True:
        print("\n" + "="*30 + "\n      야찌(Yahtzee) 게임\n" + "="*30)
        print("1. CPU와 대결\n2. 플레이어끼리 대결\n3. CPU끼리 대결\n4. CPU 성능 분석\n5. 종료")
        mode = input("모드 선택 (1-5): ").strip()
        players = []

        if mode == '1':
            player_name = input("플레이어 이름 입력: ").strip() or "Player 1"
            players.append({'name': player_name, 'is_cpu': False, 'type': None, 'scoreboard': {c: None for c in CATEGORIES}})
            print("상대할 CPU 유형 선택:")
            for i, cpu_type in enumerate(CPU_TYPES, 1):
                print(f"{i}. {cpu_type}")
            while True:
                t = input(f"선택 (1-{len(CPU_TYPES)}): ").strip()
                if t.isdigit() and 1 <= int(t) <= len(CPU_TYPES):
                    cpu_type = CPU_TYPES[int(t) - 1]
                    players.append({'name': f"CPU({cpu_type})", 'is_cpu': True, 'type': cpu_type, 'scoreboard': {c: None for c in CATEGORIES}})
                    break
                else:
                    print("잘못된 입력입니다.")
        
        elif mode == '2':
            num_players = int(input("플레이어 수 (2-4): ").strip() or "2")
            for i in range(num_players):
                pname = input(f"플레이어{i+1} 이름: ").strip() or f"Player {i+1}"
                players.append({'name': pname, 'is_cpu': False, 'type': None, 'scoreboard': {c: None for c in CATEGORIES}})

        elif mode == '3':
            for cpu_type in CPU_TYPES:
                players.append({'name': f"CPU({cpu_type})", 'is_cpu': True, 'type': cpu_type, 'scoreboard': {c: None for c in CATEGORIES}})

        elif mode == '4':
            print("\n분석할 CPU 유형 선택:")
            for i, cpu_type in enumerate(CPU_TYPES, 1):
                print(f"{i}. {cpu_type}")
            while True:
                t = input(f"선택 (1-{len(CPU_TYPES)}): ").strip()
                if t.isdigit() and 1 <= int(t) <= len(CPU_TYPES):
                    selected_cpu = CPU_TYPES[int(t) - 1]
                    try:
                        sim_count = int(input("시뮬레이션 횟수 (예: 100): "))
                    except ValueError:
                        sim_count = 100
                    analyze_cpu_performance(selected_cpu, sim_count)
                    break
                else:
                    print("잘못된 입력입니다.")
            continue

        elif mode == '5':
            print("게임을 종료합니다."); break
        else:
            print("잘못된 선택입니다."); continue

        player_logs = {}
        for turn in range(1, 13):
            print(f"\n--- {turn} 라운드 ---")
            for p in players:
                play_turn(p, turn, player_logs)

        print_final_scores(players)

        if any(not p['is_cpu'] for p in players):
            if input("\n게임 로그를 저장하시겠습니까? (y/n): ").lower() == 'y':
                save_all_logs(player_logs)