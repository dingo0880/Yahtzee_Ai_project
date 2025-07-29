[Read this in Korean](./README.ko.md)

# 🎲 Yahtzee AI: A Research Platform for Decision-Making Agents

[![Python Version](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-v2.5%20Completed-success)]()
[![Latest Commit](https://img.shields.io/github/last-commit/dingo0880/Yahtzee_Ai_project)](https://github.com/dingo0880/Yahtzee_Ai_project/commits/main)

**A research platform for developing AI agents that emulate and surpass human decision-making. This project uses the Yahtzee game environment to explore the evolution of strategic thinking in AI and to collect player data for machine learning models.**

---

<br>

## 🎬 Project Demonstration

* **v2.5 Final Version Gameplay**

    ![v2.5 Gameplay Demo](./assets/play.gif)

* **AI Performance Analysis Mode**

    ![AI Performance Analysis](./assets/statistics.png)

<br>

## 📖 Introduction

The ultimate goal of this project is to **develop a machine learning (ML) based AI agent that learns optimal strategies from human play data.** As a first step toward this goal, this Yahtzee application was built to serve as both a **data collection platform** and a **testbed** for evaluating AI performance.

Beyond simple game implementation, this is a journey to answer the fundamental question: "What constitutes an optimal decision?" To establish **baseline models** for comparison with future ML agents, I progressively developed and analyzed the limitations of various AIs, from a rule-based model mimicking human intuition to a mathematically optimized Monte Carlo simulation agent.

<br>

## ✨ Key Features

-   **Core Features for Data Collection:**
    -   **Game Log Saving:** Automatically saves every player's `State` and `Action` to a `.txt` file for future use as an ML dataset.
    -   **State Save & Load:** Saves and restores the complete game state using `JSON` files, facilitating long-term data collection and testing.
-   **Evolution of AI Decision Models:**
    -   **v0.1 (Rule/Probability-based):** A baseline AI mimicking human intuition and play styles.
    -   **v1.0 (Flawed MC):** The initial implementation of Monte Carlo simulation, which contained a critical error in its perception of "time" (remaining rolls).
    -   **v1.5 (Fixed MC):** The first correctly functioning simulation AI after resolving the fundamental flaw from v1.0.
    -   **v2.0 (Advanced Strategy AI):** An enhanced version equipped with advanced strategies like 'Strategic Sacrifice' and 'Dynamic Weights'.
-   **A Complete Experimental Environment:**
    -   **Multiple Game Modes:** Provides diverse experimental setups, including Player vs. CPU, Player vs. Player, and CPU vs. CPU.
    -   **v2.5 (Final Application):** A stable application with all convenience features added.

<br>


## CPU Players with Distinct Personalities:

- 🤖 Elite (The Strategist): The final and most advanced AI in this project. It combines Monte Carlo simulation with advanced strategies (Strategic Sacrifice, Dynamic Weights) to find the mathematically optimal move in any situation. It is a strategist that achieves the highest and most stable average score.

- 🎰 Gambler (The Risk-Taker): A rule/probability-based AI. It mimics human intuition rather than pursuing mathematical optimization, resulting in unpredictable gameplay with high variance (high highs and low lows). It is a risk-taker.

- ⚔️ Aggressive (The Attacker): An aggressive AI that prioritizes high-scoring combinations in the lower section, such as Yahtzee and Full House.

- 🛡️ Defensive (The Planner): A stable AI that focuses on securing the 35-point upper section bonus as its primary goal.

- 🧐 Normal (The Standard): A balanced AI that prioritizes standard combinations like Straights and pairs.

<br>

## 🛠️ Tech Stack

-   **Language:** `Python`
-   **Libraries:** `Pandas`, `itertools`, `json`

<br>

## ⚙️ Installation & Usage

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/dingo0880/Yahtzee_Ai_project.git](https://github.com/dingo0880/Yahtzee_Ai_project.git)
    cd Yahtzee_Ai_project
    ```
2.  **Install necessary libraries:**
    ```bash
    pip install pandas
    ```
3.  **Run the program:**
    ```bash
    python yahtzee_ai.py
    ```

<br>

## 🧠 AI Development Process & Core Logic

The core of this project is the evolutionary journey of the AI. The code for each version can be reviewed in the **[Commit History](https://github.com/dingo0880/Yahtzee_Ai_project/commits/main)**.

### v0.1: Translating Human Intuition into Code - The Rule-Based AI
The initial AI was designed with a complex system of rules and probability weights to emulate human play styles like 'Aggressive' or 'Defensive'. While this produced unpredictable gameplay, it had a clear limitation of making greedy, short-sighted decisions and failing to find optimal plays.

### v1.0 & v1.5: Adopting Monte Carlo Simulation for Higher-Level Decision Making
To overcome the limitations of the rule-based approach, I first introduced Monte Carlo simulation for mathematical optimization. However, during this process, I discovered a **critical logical flaw where the AI miscalculated the 'number of remaining rolls.'** After analyzing this failure, I refactored the system architecture to pass a `rolls_left` state variable, finally completing a correctly functioning simulation AI (v1.5).

### v2.0 ~ v2.5: Beyond AI Design to a Complete, User-Friendly Application
I completed the AI's "brain" by adding advanced strategies like **'Dynamic Weights'** and **'Strategic Sacrifice'** to the normalized simulation AI (v2.0). Subsequently, to maximize user convenience, I added features such as **'Save/Load' and 'Replay'**, finalizing the project as a complete piece of software (v2.5).

> **[Detailed Development Process & Code Analysis (Blog Link)]**

<br>

## 🚀 Future Plans

-   **Phase 2: Data Collection Backend Development**
    -   I plan to build an API server using `Django` and `MySQL` to automate and scale the collection of all play logs into a central database.
-   **Phase 3: Machine Learning-Based AI Development**
    -   The ultimate goal is to develop a new 'learning-based AI' using the collected human player data, aiming to surpass the performance of the current simulation-based AI.

<br>

## 🤔 What I Learned

-   **The Clear Limitations of Rule-Based AI:** While designing the initial AI, I experienced the limits of modeling complex human intuition with `if/else` statements and probabilities. No matter how elaborate the rules, they could not cover all edge cases, leading to performance instability.
-   **Collaboration with and Control over Generative AI:** Although this project was developed with the assistance of generative AI, I learned that the developer is ultimately responsible for the entire debugging, bug-fixing, and code design process. It was also a learning experience in prompt engineering to effectively control and direct the AI, correcting its tendencies to modify game rules, omit code, or add features arbitrarily.
-   **Understanding System Architecture Through Bug Fixing:** Fixing the 'remaining rolls' bug was not a one-line change. It required **refactoring the data flow of the entire system**, from the main game loop down to the deepest prediction function, to pass a state variable. This experience provided a practical understanding of how a small logical error can impact the entire system architecture.
