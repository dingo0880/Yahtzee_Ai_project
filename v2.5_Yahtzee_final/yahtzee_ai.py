import random
from collections import Counter
import pandas as pd
import time
import os
import sys
import itertools
import json

# --- 기본 설정 ---
SAVE_FILE = "yahtzee_save.json"

CATEGORIES = [
    "Ones", "Twos", "Threes", "Fours", "Fives", "Sixes",
    "Four of a Kind", "Full House",
    "Small Straight", "Large Straight", "Yahtzee", "Chance"
]

CPU_TYPES = ["엘리트형", "도박형", "공격형", "안정형", "일반형"]

BASE_WEIGHTS = {
    "Ones": 0.3, "Twos": 0.4, "Threes": 0.6, "Fours": 0.8,
    "Fives": 1.0, "Sixes": 1.2, "Four of a Kind": 1.8, "Full House": 2.0,
    "Small Straight": 1.1, "Large Straight": 1.6, "Yahtzee": 3.0, "Chance": 1.0
}

# --- 점수 계산 및 헬퍼 함수 ---
def score_category(dice, category):
    """카테고리별 점수를 계산하는 함수"""
    counts = Counter(dice)
    dice_set = set(dice)
    if category == "Ones": return dice.count(1)
    if category == "Twos": return dice.count(2) * 2
    if category == "Threes": return dice.count(3) * 3
    if category == "Fours": return dice.count(4) * 4
    if category == "Fives": return dice.count(5) * 5
    if category == "Sixes": return dice.count(6) * 6
    if category == "Four of a Kind": return sum(dice) if max(counts.values()) >= 4 else 0
    if category == "Full House": return 25 if sorted(counts.values()) == [2, 3] else 0
    if category == "Small Straight":
        unique_dice = sorted(list(dice_set))
        if len(unique_dice) < 4: return 0
        for i in range(len(unique_dice) - 3):
            if unique_dice[i+1] == unique_dice[i]+1 and unique_dice[i+2] == unique_dice[i]+2 and unique_dice[i+3] == unique_dice[i]+3:
                return 15
        return 0
    if category == "Large Straight":
        sorted_dice = sorted(list(dice_set))
        if len(sorted_dice) == 5 and (sorted_dice[4] - sorted_dice[0] == 4):
            return 30
        return 0
    if category == "Yahtzee": return 50 if 5 in counts.values() else 0
    if category == "Chance": return sum(dice)
    return 0

def calculate_upper_score(scoreboard):
    return sum(score for cat, score in scoreboard.items() if cat in CATEGORIES[:6] and score is not None)

def calculate_bonus(upper_score):
    return 35 if upper_score >= 63 else 0

# --- AI 핵심 두뇌 (v2.0 엘리트형) ---
def dynamic_weights_elite(turn, scoreboard):
    w = BASE_WEIGHTS.copy()
    upper_score = calculate_upper_score(scoreboard)
    upper_categories_left = [c for c in CATEGORIES[:6] if scoreboard[c] is None]

    if upper_score < 63 and upper_categories_left:
        urgency_factor = 1.0 + ((12 - turn) / 10.0)
        for cat in upper_categories_left:
            w[cat] *= (1.5 * urgency_factor)

    if turn >= 8 or upper_score >= 63:
        for cat in ("Yahtzee", "Full House", "Large Straight", "Four of a Kind"):
            if scoreboard.get(cat) is None:
                w[cat] *= 1.5
    return w

def cpu_select_category_elite(dice, scoreboard, turn):
    """
    [v2.1 수정] 단순 가중치 계산을 뛰어넘는 '최우선 순위 규칙'을 추가하여,
    희귀하고 높은 가치의 족보를 놓치지 않도록 수정한 최종 선택 함수입니다.
    """
    possible = [c for c, s in scoreboard.items() if s is None]
    if not possible: return "Chance"

    scores = {cat: score_category(dice, cat) for cat in possible}

    # --- 최우선 순위 규칙: '이건 무조건 잡아야 한다' ---
    # 1. 야찌, 라지 스트레이트, 풀하우스가 나왔다면, 다른 어떤 것도 계산하지 말고 즉시 선택한다.
    high_value_fixed = ["Yahtzee", "Large Straight", "Full House"]
    for cat in high_value_fixed:
        if cat in scores and scores[cat] > 0:
            return cat

    # 2. 스몰 스트레이트가 나왔다면, 초반(8턴 이전)에는 무조건 선택한다.
    if "Small Straight" in scores and scores["Small Straight"] > 0 and turn <= 8:
        return "Small Straight"

    # --- 위의 경우가 아니라면, 기존의 가중치 기반 계산을 수행 ---
    w = dynamic_weights_elite(turn, scoreboard)
    weighted_scores = sorted([(c, scores[c] * w.get(c, 1.0)) for c in possible], key=lambda x: x[1], reverse=True)
    
    best_choice = weighted_scores[0][0]
    best_raw_score = scores[best_choice]

    # --- 마지막 방어선: '전략적 희생' 로직 ---
    if best_raw_score < 5 and turn < 11:
        sacrifice_priority = ["Yahtzee", "Ones", "Twos", "Chance"]
        for sac_cat in sacrifice_priority:
            if scoreboard.get(sac_cat) is None and scores[sac_cat] == 0:
                return sac_cat
                
    return best_choice

def estimate_expected_score(dice, keep_idxs, scoreboard, turn, rolls_left, n_sim=200):
    total = 0
    for _ in range(n_sim):
        sim_dice = dice.copy()
        reroll_indices = [i for i in range(5) if i not in keep_idxs]
        
        for _ in range(rolls_left):
            for i in reroll_indices:
                sim_dice[i] = random.randint(1, 6)
        
        best_cat = cpu_select_category_elite(sim_dice, scoreboard, turn)
        total += score_category(sim_dice, best_cat)
    return total / n_sim

def get_recommended_target(dice, scoreboard, turn):
    w = dynamic_weights_elite(turn, scoreboard)
    possible = [c for c, s in scoreboard.items() if s is None]
    if not possible: return "Chance"
    return max(possible, key=lambda c: score_category(dice, c) * w.get(c, 1.0))

# --- [복구] 도박형 및 기타 AI를 위한 규칙 기반 로직 ---
def get_recommended_target_gambler(dice, scoreboard):
    possible = [c for c, s in scoreboard.items() if s is None]
    if not possible: return "Chance"
    return max(possible, key=lambda c: score_category(dice, c) * BASE_WEIGHTS.get(c, 1.0))

def cpu_select_category_simple(dice, scoreboard):
    possible = [c for c, s in scoreboard.items() if s is None]
    if not possible: return "Chance"
    return max(possible, key=lambda cat: score_category(dice, cat))

# --- 각 CPU 유형별 전략 함수 ---
def strategic_keep_elite(dice, scoreboard, turn, rolls_left):
    counts = Counter(dice)
    candidates = [list(c) for r in range(6) for c in itertools.combinations(range(5), r)]
    if counts:
        top = counts.most_common(1)[0][0]
        candidates.append([i for i, d in enumerate(dice) if d == top])
    rec = get_recommended_target(dice, scoreboard, turn)
    if rec in CATEGORIES[:6]:
        face = CATEGORIES.index(rec) + 1
        candidates.append([i for i, d in enumerate(dice) if d == face])
    unique_cands = []
    for c in candidates:
        sorted_c = sorted(c)
        if sorted_c not in [sorted(uc) for uc in unique_cands]:
            unique_cands.append(c)
    best_keep, best_ev = [], -1
    for keep_idxs in unique_cands:
        ev = estimate_expected_score(dice, keep_idxs, scoreboard, turn, rolls_left)
        if ev > best_ev:
            best_ev, best_keep = ev, keep_idxs
    return best_keep

def strategic_keep_gambler(dice, scoreboard):
    counts = Counter(dice)
    if scoreboard.get("Yahtzee") is None and counts.most_common(1) and counts.most_common(1)[0][1] >= 4:
        return [i for i,d in enumerate(dice) if d==counts.most_common(1)[0][0]]
    if scoreboard.get("Full House") is None and sorted(counts.values())==[2,3]:
        return list(range(5))
    tgt = get_recommended_target_gambler(dice, scoreboard)
    if not tgt: return list(range(5))
    keep_indices = []
    if tgt in CATEGORIES[:6]:
        keep_indices = [i for i,d in enumerate(dice) if d==CATEGORIES.index(tgt)+1]
    elif tgt in ("Four of a Kind","Yahtzee"):
        if counts: keep_indices = [i for i,d in enumerate(dice) if d==counts.most_common(1)[0][0]]
    elif tgt == "Full House":
        if sorted(counts.values()) == [2,3]: return list(range(5))
        nums_to_keep = [num for num, count in counts.items() if count in [2,3]]
        if nums_to_keep: keep_indices = [i for i,d in enumerate(dice) if d in nums_to_keep]
    elif tgt in ("Small Straight", "Large Straight"):
        dice_set = sorted(list(set(dice)))
        if not dice_set: return []
        best_seq = []
        current_seq = [dice_set[0]]
        for i in range(1, len(dice_set)):
            if dice_set[i] == dice_set[i-1] + 1: current_seq.append(dice_set[i])
            else:
                if len(current_seq) > len(best_seq): best_seq = current_seq
                current_seq = [dice_set[i]]
        if len(current_seq) > len(best_seq): best_seq = current_seq
        if len(best_seq) >= 3: keep_indices = [i for i,d in enumerate(dice) if d in best_seq]
    if not keep_indices and counts:
         keep_indices = [i for i,d in enumerate(dice) if d==counts.most_common(1)[0][0]]
    return keep_indices

def strategic_keep_attack(dice, scoreboard, turn):
    counts = Counter(dice)
    if scoreboard.get("Yahtzee") is None and counts.most_common(1) and counts.most_common(1)[0][1] >= 3:
        return [i for i, d in enumerate(dice) if d == counts.most_common(1)[0][0]]
    if scoreboard.get("Full House") is None and sorted(counts.values()) == [2, 3]:
        return list(range(5))
    rec = get_recommended_target(dice, scoreboard, turn)
    if rec in CATEGORIES[:6]:
        return [i for i, d in enumerate(dice) if d == CATEGORIES.index(rec) + 1]
    if counts: return [i for i, d in enumerate(dice) if d == counts.most_common(1)[0][0]]
    return []

def strategic_keep_defense(dice, scoreboard, turn):
    counts = Counter(dice)
    upper_score = calculate_upper_score(scoreboard)
    remain_upper = [c for c in CATEGORIES[:6] if scoreboard[c] is None]
    if upper_score < 63 and remain_upper:
        rec = max(remain_upper, key=lambda c: score_category(dice, c))
        face = CATEGORIES.index(rec) + 1
        return [i for i, d in enumerate(dice) if d == face]
    possible = [c for c, s in scoreboard.items() if s is None]
    if not possible: return list(range(5))
    rec = max(possible, key=lambda c: score_category(dice, c))
    if rec in CATEGORIES[:6]:
        return [i for i, d in enumerate(dice) if d == CATEGORIES.index(rec) + 1]
    if counts: return [i for i, d in enumerate(dice) if d == counts.most_common(1)[0][0]]
    return []

def strategic_keep_normal(dice, scoreboard, turn):
    counts = Counter(dice)
    patterns = {"Small Straight": [[1, 2, 3, 4], [2, 3, 4, 5], [3, 4, 5, 6]],
                "Large Straight": [[1, 2, 3, 4, 5], [2, 3, 4, 5, 6]]}
    for cat, pats in patterns.items():
        if scoreboard.get(cat) is None:
            for pat in pats:
                if set(pat).issubset(set(dice)):
                    return [i for i, d in enumerate(dice) if d in pat]
    rec = get_recommended_target(dice, scoreboard, turn)
    if rec in CATEGORIES[:6]:
        return [i for i, d in enumerate(dice) if d == CATEGORIES.index(rec) + 1]
    if counts: return [i for i, d in enumerate(dice) if d == counts.most_common(1)[0][0]]
    return []

def strategic_decide_dice_to_keep(dice, scoreboard, turn, cpu_type, rolls_left=2):
    if cpu_type == "엘리트형": return strategic_keep_elite(dice, scoreboard, turn, rolls_left)
    if cpu_type == "도박형": return strategic_keep_gambler(dice, scoreboard)
    if cpu_type == "공격형": return strategic_keep_attack(dice, scoreboard, turn)
    if cpu_type == "안정형": return strategic_keep_defense(dice, scoreboard, turn)
    return strategic_keep_normal(dice, scoreboard, turn)

def cpu_select_category_dispatcher(dice, scoreboard, cpu_type, turn):
    if cpu_type == "엘리트형":
        return cpu_select_category_elite(dice, scoreboard, turn)
    else: # 도박형, 공격형, 안정형, 일반형은 동일한 단순 선택 로직 사용
        return cpu_select_category_simple(dice, scoreboard)

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
        
        rolls_left = 3 - r
        if is_cpu:
            keep_indices = strategic_decide_dice_to_keep(dice, scoreboard, turn_num, cpu_type, rolls_left)
            if len(keep_indices) == 5:
                print("CPU: 모든 주사위 고정.")
                break
            print(f"CPU ({cpu_type}) 고정: {[dice[i] for i in keep_indices]}")
            time.sleep(1)
            new_dice = [d for i, d in enumerate(dice) if i in keep_indices]
            new_dice.extend([random.randint(1, 6) for _ in range(5 - len(new_dice))])
            dice = new_dice
        else: # 사람 플레이어
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
        choice = cpu_select_category_dispatcher(dice, scoreboard, cpu_type, turn_num)
    else: # 사람 플레이어
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
                print("\n\U0001F504 남은 굴림을 계속 진행합니다.")
                for r_cont in range(roll_number + 1, 4):
                    roll_number = r_cont
                    print(f"\n--- {r_cont}차 굴림 ---")
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

def run_single_game_simulation(cpu_type):
    scoreboard = {c: None for c in CATEGORIES}
    for turn in range(1, 13):
        dice = [random.randint(1, 6) for _ in range(5)]
        for r in range(2):
            rolls_left = 2 - r
            keep = strategic_decide_dice_to_keep(dice, scoreboard, turn, cpu_type, rolls_left)
            if len(keep) == 5: break
            
            new_dice = [d for i, d in enumerate(dice) if i in keep]
            reroll_count = 5 - len(new_dice)
            new_dice.extend([random.randint(1, 6) for _ in range(reroll_count)])
            dice = new_dice
        
        choice = cpu_select_category_dispatcher(dice, scoreboard, cpu_type, turn)
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

def save_progress(players, turn):
    with open(SAVE_FILE, 'w', encoding='utf-8') as f:
        json.dump({"turn": turn, "players": players}, f, ensure_ascii=False, indent=2)

def load_progress():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return data["players"], data["turn"]
        except (json.JSONDecodeError, KeyError):
            print("⚠️ 저장 파일이 손상되었습니다. 새 게임을 시작합니다.")
            return None, None
    return None, None

# --- 메인 실행 ---
if __name__ == '__main__':
    while True:
        print("\n" + "="*30 + "\n      야찌(Yahtzee) 게임\n" + "="*30)
        print("1. CPU와 대결\n2. 플레이어끼리 대결\n3. CPU끼리 대결\n4. CPU 성능 분석\n5. 이어서 하기\n6. 종료")
        mode = input("모드 선택 (1-6): ").strip()
        players = []
        start_turn = 1
        game_started = False

        if mode == '1':
            name = input("플레이어 이름 입력: ").strip() or "Player 1"
            players.append({'name': name, 'is_cpu': False, 'type': None, 'scoreboard': {c: None for c in CATEGORIES}})
            print("상대할 CPU 유형 선택:")
            for i, cpu_type in enumerate(CPU_TYPES, 1):
                print(f"{i}. {cpu_type}")
            while True:
                t = input(f"선택 (1-{len(CPU_TYPES)}): ").strip()
                if t.isdigit() and 1 <= int(t) <= len(CPU_TYPES):
                    cpu_type = CPU_TYPES[int(t) - 1]
                    players.append({'name': f"CPU({cpu_type})", 'is_cpu': True, 'type': cpu_type, 'scoreboard': {c: None for c in CATEGORIES}})
                    game_started = True
                    break
                else:
                    print("잘못된 입력입니다.")

        elif mode == '2':
            while True:
                try:
                    num_players = int(input("플레이어 수 입력 (2~4명): "))
                    if 2 <= num_players <= 4:
                        break
                    else:
                        print("⚠️ 2명 이상 4명 이하만 가능합니다.")
                except ValueError:
                    print("⚠️ 숫자를 입력해주세요.")
            for i in range(1, num_players + 1):
                name = input(f"플레이어 {i} 이름 입력: ").strip() or f"Player {i}"
                players.append({'name': name, 'is_cpu': False, 'type': None, 'scoreboard': {c: None for c in CATEGORIES}})
            game_started = True

        elif mode == '3':
            for cpu_type in CPU_TYPES:
                players.append({'name': f"CPU({cpu_type})", 'is_cpu': True, 'type': cpu_type, 'scoreboard': {c: None for c in CATEGORIES}})
            game_started = True

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
                        if sim_count <= 0: sim_count = 100
                    except ValueError:
                        sim_count = 100
                    analyze_cpu_performance(selected_cpu, sim_count)
                    break
                else:
                    print("잘못된 입력입니다.")
            continue

        elif mode == '5':
            players, start_turn = load_progress()
            if players is None:
                continue
            print(f"불러온 게임 ▶ 플레이어 수: {len(players)}명, 진행 라운드: {start_turn}부터")
            for p in players:
                display_scoreboard(p['name'], p['scoreboard'])
            game_started = True

        elif mode == '6':
            print("게임을 종료합니다.")
            break

        else:
            print("잘못된 선택입니다."); continue

        if game_started:
            player_logs = {}
            for turn in range(start_turn, 13):
                print(f"\n--- {turn} 라운드 ---")
                for p in players:
                    play_turn(p, turn, player_logs)
                save_progress(players, turn + 1)

            print_final_scores(players)
            if os.path.exists(SAVE_FILE):
                os.remove(SAVE_FILE)

            if any(not p['is_cpu'] for p in players):
                if input("\n게임 로그를 저장하시겠습니까? (y/n): ").lower() == 'y':
                    save_all_logs(player_logs)

            replay = input("\n다시 플레이하시겠습니까? (y/n): ").strip().lower()
            if replay != 'y':
                print("게임을 종료합니다.")
                break
