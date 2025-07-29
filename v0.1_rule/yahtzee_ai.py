import random
import time
from collections import Counter

# --- 기본 설정 ---
CATEGORIES = [
    "Ones", "Twos", "Threes", "Fours", "Fives", "Sixes",
    "Four of a Kind", "Full House",
    "Small Straight", "Large Straight", "Yahtzee", "Chance"
]

CPU_TYPES = ["안정형", "공격형", "일반형", "랜덤"]

# --- 점수 계산 함수 ---
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
        # 4개 이상 연속된 숫자가 있는지 확인
        unique_dice = sorted(list(dice_set))
        if len(unique_dice) < 4: return 0
        for i in range(len(unique_dice) - 3):
            if unique_dice[i+3] - unique_dice[i] == 3:
                return 15
        return 0
    if category == "Large Straight":
        # 5개 연속된 숫자가 있는지 확인
        sorted_dice = sorted(list(dice_set))
        if len(sorted_dice) == 5 and (sorted_dice[4] - sorted_dice[0] == 4):
            return 30
        return 0
    if category == "Yahtzee": return 50 if 5 in counts.values() else 0
    if category == "Chance": return sum(dice)
    return 0

def calculate_upper_score(scoreboard):
    """상단 점수 합계를 계산하는 함수"""
    return sum(score for cat, score in scoreboard.items() if cat in CATEGORIES[:6] and score is not None)

def calculate_bonus(upper_score):
    """상단 보너스 점수를 계산하는 함수"""
    return 35 if upper_score >= 63 else 0

# --- UI 관련 함수 ---
def display_scoreboard_with_bonus(player_name, scoreboard):
    """점수판을 보너스와 함께 출력하는 함수"""
    upper_score = calculate_upper_score(scoreboard)
    bonus = calculate_bonus(upper_score)
    lower_score = sum(score for cat, score in scoreboard.items() if cat not in CATEGORIES[:6] and score is not None)
    total_score = upper_score + bonus + lower_score

    print(f"\n===== {player_name}의 점수판 =====")
    for idx, cat in enumerate(CATEGORIES, 1):
        val = scoreboard.get(cat)
        print(f"{idx:2}. {cat:<15}: {val if val is not None else '-'}")
    print("-------------------------")
    print(f"상단 합계: {upper_score} / 63  (보너스: +{bonus})")
    print(f"총합: {total_score}")
    print("===================")

def display_dice_with_indices(dice):
    """현재 주사위와 인덱스를 출력하는 함수"""
    print("\n현재 주사위:")
    for i, d in enumerate(dice, 1):
        print(f"  {i}: 🎲 {d}")

# --- CPU AI 로직 함수 ---
def find_best_straight_hold(dice):
    """스트레이트를 만들기 위해 남길 최적의 주사위를 찾는 함수"""
    unique_dice = sorted(set(dice))
    if not unique_dice: return []
    
    best_seq = []
    current_seq = [unique_dice[0]]
    for i in range(1, len(unique_dice)):
        if unique_dice[i] == unique_dice[i-1] + 1:
            current_seq.append(unique_dice[i])
        else:
            if len(current_seq) > len(best_seq):
                best_seq = current_seq
            current_seq = [unique_dice[i]]
    if len(current_seq) > len(best_seq):
        best_seq = current_seq
        
    return best_seq

def strategic_decide_dice_to_keep(dice, scoreboard, turn_num, cpu_type):
    """CPU 유형과 게임 상황에 따라 남길 주사위를 결정하는 메인 전략 함수"""
    counts = Counter(dice)
    
    # 1. Yahtzee, Four of a Kind, Full House 시도 (모든 단계에서 높은 우선순위)
    for num, count in counts.items():
        if count >= 3:
            if scoreboard["Yahtzee"] is None or scoreboard["Four of a Kind"] is None:
                return [i for i, d in enumerate(dice) if d == num]
    if sorted(counts.values()) == [2, 2]: # Two Pair -> Full House 시도
        if scoreboard["Full House"] is None:
            pair_nums = [num for num, count in counts.items() if count == 2]
            return [i for i, d in enumerate(dice) if d == max(pair_nums)]

    # 2. 스트레이트 시도
    straight_open = scoreboard["Small Straight"] is None or scoreboard["Large Straight"] is None
    if straight_open:
        hold_numbers = find_best_straight_hold(dice)
        if len(hold_numbers) >= 3: # 3개 이상 연속되면 스트레이트 시도 가치가 있음
            return [i for i, d in enumerate(dice) if d in hold_numbers]
            
    # 3. 상단 보너스를 위한 전략
    upper_score = calculate_upper_score(scoreboard)
    if upper_score < 63:
        for num in range(6, 0, -1):
            category = CATEGORIES[num-1]
            if scoreboard[category] is None and num in dice:
                if cpu_type == "안정형" and dice.count(num) >= 2:
                    return [i for i, d in enumerate(dice) if d == num]
                elif dice.count(num) >= 3:
                    return [i for i, d in enumerate(dice) if d == num]

    # 4. 공격형을 위한 특별 전략
    if cpu_type == "공격형":
        for num in [6, 5]:
            if dice.count(num) >= 2:
                return [i for i, d in enumerate(dice) if d == num]

    # 5. 기본 전략: 가장 많이 나온 숫자 중 가장 높은 숫자를 남김
    if counts:
        max_count = counts.most_common(1)[0][1]
        best_num_to_keep = max([num for num, count in counts.items() if count == max_count])
        return [i for i, d in enumerate(dice) if d == best_num_to_keep]

    return []

def weighted_choice(choices):
    """가중치 기반으로 하나를 선택하는 함수"""
    total = sum(weight for _, weight in choices)
    if total == 0: return choices[0][0] if choices else None
    r = random.uniform(0, total)
    upto = 0
    for choice, weight in choices:
        if upto + weight >= r:
            return choice
        upto += weight
    return choices[-1][0] if choices else None

def cpu_select_category(dice, scoreboard, turn_num, cpu_type):
    """CPU가 최종 주사위를 보고 어떤 족보에 기록할지 결정하는 함수"""
    possible = [cat for cat, score in scoreboard.items() if score is None]
    if not possible: return "Chance"

    phase = "초반" if turn_num <= 4 else "중반" if turn_num <= 8 else "후반"
    
    scores = {cat: score_category(dice, cat) for cat in possible}
    fixed_scores = {"Yahtzee": 50, "Large Straight": 30, "Full House": 25, "Small Straight": 15}
    for cat, score in fixed_scores.items():
        if cat in scores and scores[cat] >= score:
            return cat

    prob_map = {
        "안정형": {"HighValue": 60, "UpperBonus": 80, "Chance": 20},
        "공격형": {"HighValue": 80, "UpperBonus": 40, "Chance": 10},
        "일반형": {"HighValue": 70, "UpperBonus": 60, "Chance": 30},
    }
    weights = []
    
    upper_score = calculate_upper_score(scoreboard)
    
    for cat in possible:
        score = scores[cat]
        base_weight = 10
        
        if cat in ["Four of a Kind", "Yahtzee"]:
            base_weight += prob_map[cpu_type]["HighValue"] * (score / 30)
        
        if cat in CATEGORIES[:6]:
            if upper_score < 63:
                base_weight += prob_map[cpu_type]["UpperBonus"]
                if cpu_type == "안정형":
                    base_weight += 20
        
        if cat == "Chance":
            base_weight += prob_map[cpu_type]["Chance"]
            if score < 15:
                base_weight /= 4

        weights.append((cat, base_weight))

    return weighted_choice(weights)

# --- 게임 진행 관련 함수 ---
def select_cpu_type(cpu_num):
    """CPU 유형을 선택하는 함수"""
    print(f"CPU{cpu_num} 유형을 선택하세요:")
    for i, ctype in enumerate(CPU_TYPES, 1):
        print(f"{i}. {ctype}")
    while True:
        sel = input("번호 입력 (1-4): ").strip()
        if sel in ['1', '2', '3']:
            return CPU_TYPES[int(sel)-1]
        elif sel == '4':
            random_cpu_type = random.choice(["일반형", "공격형", "안정형"])
            print(f"CPU{cpu_num}은 '랜덤' 유형을 선택하여 {random_cpu_type}으로 결정되었습니다.")
            return random_cpu_type
        print("잘못된 입력입니다. 다시 선택해주세요.")

def get_possible_categories(dice, scoreboard):
    """점수를 기록할 수 있는 모든 카테고리 리스트를 반환"""
    return [cat for cat, score in scoreboard.items() if score is None]

def play_turn(player, turn_num, player_logs):
    """한 플레이어의 한 턴 전체를 관리하고 실행"""
    scoreboard = player['scoreboard']
    player_name, is_cpu, cpu_type = player['name'], player['is_cpu'], player['type']
    
    print(f"\n<<<<< {player_name}의 {turn_num}턴 >>>>>")
    dice = [random.randint(1, 6) for _ in range(5)]
    log = [f"🎲 1차 굴림: {dice}"]
    
    for roll_num in range(2, 4):
        print(f"\n--- {player_name}의 {roll_num-1}차 굴림 결과 ---")
        display_dice_with_indices(dice)
        
        if is_cpu:
            keep_indices = strategic_decide_dice_to_keep(dice, scoreboard, turn_num, cpu_type)
            if len(keep_indices) == 5:
                print(f"CPU({cpu_type}): 모든 주사위 고정.")
                break
            reroll_indices = [i for i in range(5) if i not in keep_indices]
            print(f"CPU ({cpu_type})가 재굴림할 주사위: {[i+1 for i in reroll_indices]}")
            time.sleep(1)
        else:
            raw = input(f"{roll_num}차 굴림: 재굴림할 주사위 번호 입력 (예:13, 엔터 시 중단): ").strip()
            if not raw:
                log.append("굴림 중단")
                break
            reroll_indices = {int(c) - 1 for c in raw if c.isdigit() and 1 <= int(c) <= 5}
            log.append(f"{roll_num}차 굴림 - 재굴림: {sorted([i+1 for i in reroll_indices])}")

        for i in reroll_indices:
            dice[i] = random.randint(1, 6)
        log.append(f"🎲 {roll_num}차 굴림: {dice}")

    print("\n--- 최종 주사위 ---")
    display_dice_with_indices(dice)
    
    possible = get_possible_categories(dice, scoreboard)
    
    if is_cpu:
        chosen_cat = cpu_select_category(dice, scoreboard, turn_num, cpu_type)
        print(f"\nCPU ({cpu_type})가 선택한 족보: {chosen_cat}")
    else:
        print("\n--- 기록할 족보 선택 ---")
        candidates = [(cat, score_category(dice, cat)) for cat in possible]
        for i, (cat, score) in enumerate(candidates, 1):
            print(f"{i}. {cat} ({score}점)")
        
        while True:
            sel = input(f"번호 선택 (1-{len(candidates)}): ").strip()
            if sel.isdigit() and 1 <= int(sel) <= len(candidates):
                chosen_cat = candidates[int(sel) - 1][0]
                break
            print("잘못된 입력입니다.")

    score = score_category(dice, chosen_cat)
    scoreboard[chosen_cat] = score
    log.append(f"최종 선택: {chosen_cat} ({score}점)")
    print(f"-> {chosen_cat}에 {score}점을 기록했습니다.")
    
    if not is_cpu:
        player_logs.setdefault(player_name, []).extend([f"[{turn_num}턴]"] + log)
    
    time.sleep(1)

def print_final_scores(players):
    """게임 종료 후 최종 점수와 순위를 출력"""
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

def yahtzee_game():
    """게임 모드를 선택하고 전체 게임을 실행하는 메인 함수"""
    while True:
        print("\n" + "="*30 + "\n      야찌(Yahtzee) 게임\n" + "="*30)
        print("1. CPU와 대결\n2. 플레이어끼리 대결\n3. CPU끼리 대결\n4. 종료")
        mode = input("모드 선택 (1-4): ").strip()

        if mode not in ['1', '2', '3', '4']:
            print("잘못된 선택입니다."); continue
        if mode == '4':
            print("게임을 종료합니다."); break

        players = []
        if mode == '1':
            pname = input("플레이어 이름: ").strip() or "Player 1"
            players.append({"name": pname, "is_cpu": False, "type": None, "scoreboard": {cat: None for cat in CATEGORIES}})
            num_cpus = int(input("상대할 CPU 수 (1-3): ").strip() or "1")
            for i in range(num_cpus):
                ctype = select_cpu_type(i+1)
                players.append({"name": f"CPU{i+1}", "is_cpu": True, "type": ctype, "scoreboard": {cat: None for cat in CATEGORIES}})
        elif mode == '2':
            num_players = int(input("플레이어 수 (2-4): ").strip() or "2")
            for i in range(num_players):
                pname = input(f"플레이어{i+1} 이름: ").strip() or f"Player {i+1}"
                players.append({"name": pname, "is_cpu": False, "type": None, "scoreboard": {cat: None for cat in CATEGORIES}})
        elif mode == '3':
            num_cpus = int(input("CPU 수 (2-4): ").strip() or "2")
            for i in range(num_cpus):
                ctype = select_cpu_type(i+1)
                players.append({"name": f"CPU{i+1}", "is_cpu": True, "type": ctype, "scoreboard": {cat: None for cat in CATEGORIES}})
        
        player_logs = {}
        for turn in range(1, 13):
            print(f"\n--- {turn} 라운드 ---")
            for p in players:
                play_turn(p, turn, player_logs)
                display_scoreboard_with_bonus(p['name'], p['scoreboard'])
                time.sleep(2)

        print_final_scores(players)
        
        if any(not p['is_cpu'] for p in players):
            if input("\n게임 로그를 저장하시겠습니까? (y/n): ").lower() == 'y':
                # (로그 저장 기능은 여기에 구현)
                pass

if __name__ == '__main__':
    yahtzee_game()
