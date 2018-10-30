# Halite2AI

In this repository, I will share my rule based AI for last year's Halite 2 competition, which ends up with 29th of over 1000 teams. Beside, I will include a review for Halite 2's top 3 bot in this page. I wrote this review to warm up myself for this year's Halite 3 competition. Surprisingly, I found that a lot of strategies discussed in this review is applicable to Halite 3.

In this post, I aim to give a brief review on the useful strategies and tricks for the top 3 bots in last year's Halite 2 competition. **I cherry-pick the contents from all these post-mortems majorly based on how they are likely to be able to be applied to Halite 3.** Hence there are some tricks that are important to Halite 2 but are missing here. In this way, I am trying to make this review more useful specifically for Halite 3 preperation. I also bold the sentences that I find it worthy to be highlighted.

We can see that the bots of the top players are quite different in many aspects. For example, FakePsyho suggests to use a stateless AI while ReCurs3 designs a AI with several distinctive states with each one to handle a different producure of the games.

Table of contents:
<!-- TOC depthFrom:1 depthTo:6 withLinks:1 updateOnSave:1 orderedList:0 -->

- [1st: ReCurs3](#1st-recurs3)
	- [High Level Overview](#high-level-overview)
	- [Early Game Strategy](#early-game-strategy)
		- [Colony Planning](#colony-planning)
		- [Early Game Execution](#early-game-execution)
	- [Game State Masking](#game-state-masking)
	- [Strategic Pass](#strategic-pass)
		- [Colonize Role: Securing Planet in the Future](#colonize-role-securing-planet-in-the-future)
		- [Attack/Defense Role](#attackdefense-role)
		- [Spawn Prediction](#spawn-prediction)
	- [Tactical Pass](#tactical-pass)
		- [Enemy prediction](#enemy-prediction)
		- [Grouping](#grouping)
- [2nd: FakePsyho](#2nd-fakepsyho)
	- [General Guidance](#general-guidance)
	- [Most Important Changes](#most-important-changes)
	- [Phases](#phases)
	- [Core Concept: Evaluation Function](#core-concept-evaluation-function)
	- [Core Concept: Global Greedy Assignment](#core-concept-global-greedy-assignment)
	- [Small Tricks](#small-tricks)
		- [Ideas that haven't been implemented:](#ideas-that-havent-been-implemented)
- [3rd: Shummie](#3rd-shummie)
	- [Numeric Superiority](#numeric-superiority)
	- [**Non-Aggression Pact**](#non-aggression-pact)
	- [Bot Logic Overview](#bot-logic-overview)
		- [Behaviors: Distractor](#behaviors-distractor)
		- [Navigation: Navigation Functions](#navigation-navigation-functions)
		- [Navigation Evaluation](#navigation-evaluation)
- [References](#references)

<!-- /TOC -->

# 1st: ReCurs3

For a more detailed version, please take a look at [the link to ReCurs3's Post-Mortem](https://recursive.cc/blog/halite-ii-post-mortem.html)

## High Level Overview

To get a better idea of all the parts involved, here is what happens at a high level on every game turn:

- (4p only) Survival strategy override when the game is considered lost, try to achieve the highest rank by surviving until the end.
- Early game strategy override from the start until a planet is colonized and safe of invaders.
- (4p only) Alter the game state to focus more on a single target.
- If no strategy override is present, perform a generic strategic pass, assigning a high level goal and desired target position for every allied ship.
- Perform a tactical pass, possibly modifying the action of every allied ship that could encounter an enemy, while trying to maintain it as close from the original target as possible.

## Early Game Strategy

Because the early game is so different and unforgiving, I isolated this part of the game in its own code path. The big two differences over the rest are choosing the initial planet(s) to settle on, and take into account potential rushes from the enemy, who attack straight away with their initial ships hoping for a quick win by catching bots off guard.

### Colony Planning

The choice of initial planet(s) is done once at game start, and is different between 2p games and 4p. The one for 2p is very old but I could not improve or find a replacement in time that seemed to perform as well. **The idea is to control as much space as possible early on by choosing a planet with other planets nearby, to boost early production** and be the first player to dominate the center, therefore breaking the symmetry, and typically winning the game.

4p games require another strategy, as the goal is quite different. A good spot is still desirable, but definitely not at the cost of being nearby enemy players. Otherwise, the risk of being rushed is greatly increased, and even with no rush, the risk of becoming the enemy's target of choice is also higher. Having two enemies nearby early on is almost guaranteed to turn into a bad game.

### Early Game Execution

The early game plan aims to establish the initial colonies as fast as possible while also keeping early invaders at bay. It also tries to break a stalemate in case no one colonizes by engaging combat after a while, and rushes if it owns no planet but the enemy does.

## Game State Masking

Another 4p only improvement, only enabled once the early game is over, this mask aims to force the bot to focus on one player instead of multiple at once. If a player can be eliminated more quickly, then its planets can be taken over faster and therefore create a bigger snowball effect. When no target player is assigned, the enemy having a ship closest to an allied planet is considered as the target.

## Strategic Pass

This pass is looking to do high level decision making by **assigning one of the following roles to every allied ship**:

- Colonize a planet.
- Defend an allied docked ship.
- Attack an enemy docked ship.

Either looping through targets to find a ship to assign to, or looping through ships to find a target, have their flaws as they will give poor solutions in some scenarios. It is important to **minimize the sum of all distances between ships and their targets in order to respond faster overall.** I thought of using an evolutionary search for that, but decided to start with a simpler algorithm at first and see if it needs replacement later. It survived in almost intact shape since.

- For all allied ships that are undocked:
	- For each possible role, compute the best target for that role and give it a score.
	- Push that role-score pair in a list.
- Sort the list of all role-score pairs by their score (lower score = better).
- Looping through the pairs of sorted list:
	- If the ship of that pair already has a role, ignore and proceed to the next pair.
	- Try to assign this role to the ship. If it fails (more on this later), compute a different target for that role and use its new score to insert it at the appropriate slot in the list.
	- If assignment is successful, keep the desired target position for the tactical pass.

The way the targeting, scoring and execution of a role is done is specific to each, so more details follow.

### Colonize Role: Securing Planet in the Future

For a given ship, it just tries to find the closest planet with docking spots available. However, the twist is it will exclude planets that are considered unsafe to colonize. At some point I noticed my bot was wasting a lot of ships by docking them only to get destroyed a few turns later, so I tried to figure out how to prevent that.

**The main idea to determine planet safety is making sure all nearby enemy ships can be dealt with in the future**, by checking if for each one of them, an allied ship in proximity can reach that point in time.

- Loop through all enemy ships that are less than 45 units away of the docking spot:
	- Compute the enemy distance to the docking spot.
	- Find an allied undocked ship with a distance to the docking spot that is closest to the enemy's distance, but no more than 7 units above.
		- If no such ship is found, the planet is unsafe. Bail out.
	- This allied ship is now excluded from further iterations of the loop.
- If the loop was completed without bailing out, the planet is safe.

The score given to that role is the distance to the planet's surface. A -40 bonus is added if the ship can already dock, to not get distracted when it's already almost colonized anyway. The assignment of this role fails if the available docking spots are already reserved by other ships, or if the planet becomes unsafe due to assignment of other roles.

### Attack/Defense Role

For good or bad reasons, I decided a ship cannot be a candidate for both attack and defense at once. I thought it would be easier to balance priorities between colonizing vs fighting and attacking vs defending rather than everything at once, but cannot say whether it was better or not in the end.

For defense, only enemy ships near an allied docked ship are considered. For attack, for a long while all enemy ships were considered. At some point I experimented with being exclusively focused on doing economic damage and found a remarkable improvement in behavior and ranking. Ever since, only enemy docked ships are considered for attack.

### Spawn Prediction

An important detail of the strategic pass is it does a small alteration of the game state while computing roles. Given the current state, **it looks at ships that will be produced by allied planets in the next 10 turns and adds them to the state using the position closest to map center regardless of ship proximity**. Those ships will have a distance penalty assigned corresponding to 8 * numTurns. This means that every distance calculation in which these ships are involved get that penalty added as a distance. The implications of this alteration are considerable. It frees up a number of current ships to perform better roles, leaving some for future ships instead. For instance, it might choose not to bother defending and attack instead, or not send a ship to colonize a planet that will produce a ship to colonize with faster.

No prediction was done for the enemy as no behavior or ranking improvement could be found, sometimes even being detrimental.

## Tactical Pass

Once every ship has been assigned a role, **the tactical pass aims to use better moves than the one provided by the strategic pass, to still accomplish those roles but with better positioning.**

**Proper ship micromanagement makes a huge difference in Halite.** Superior ship numbers in combat snowballs hard, avoiding useless fights lets ships focus on more important tasks and evading defenses can let ships harass better, etc. Given the combat mechanics it seemed really difficult to come up with a decision making structure similar to the other parts. Maybe some sort of tree search could help figure out the best movements, but the very large number of possible moves even with pruning, especially given the quantities of ships involved, did not seem feasible in any straightforward fashion.

So I started looking at a simpler version of the problem: **if enemy movements are known in advance, how to position ships to take the most advantage of it?** This was more or less my first iteration:

- Assume all enemy ships move towards their closest enemy ship at full thrust.
- Simulate all ship movements and attacks, including the instantaneous attacks of the next turn.
- Evaluate the score of this simulation by summing all allied ships health, and subtracting the sum of all enemy ships health.

This gives a baseline for the current plan given by the strategic pass, which can then be iterated on to find moves giving a better score. I used hill climbing to refine the current plan:

- Take an allied undocked ship at random.
- Replace its action with a move of random angle and thrust.
- Perform the simulation again and evaluate the new score. If it's better than the old one, replace that ship's action with the random one.
- Repeat until timeout.

With this iterative search the bot's behavior was already massively improved. Ships would avoid losing battles by moving out of the way, or commit together to ensure the battle result would get even better. Emergent behavior, such as low health ships attempting to ram into an enemy, would happen as long the net health result is better. Afterwards it was all about adding various improvements to this basic idea.

### Enemy prediction

So far it's been assumed the enemy ship always move straight towards the closest target. It's obviously not something that happens very often, so moves can be made that are very weak to other enemy responses. I experimented quite a lot with various probability models and ended up settling with this one. A set of 19 global enemy responses is precomputed, and the evaluation of each resulting simulation is summed up to make a single score. In other words, each tested move results in 19 different simulations and making sure the score is better on average. For enemy ship movement, I also disabled ship-ship collisions if the two ships involved belong to the enemy, in order to spend less time solving it and overestimate the enemy's ability to group up together to get a more conservative prediction. Ship-planet collisions however are always maintained.

### Grouping

Unlike many other top bots, I did not have any specific code forcing ships to move closer together, as it created weird or undesirable behaviors. However I still used a clustering method to help the hill climbing get out of some traps. One problem I noticed is when a smaller mass of ships is engaged in combat with a bigger one, the hill climbing fails to move them individually out of danger, because the evaluation function only sees the short term impact. It thinks keeping them in the action will minimize the losses, failing to see the overall battle is lost.

So in addition to trying random actions on individual ships, it also tries applying a random action to all ships of a group and examines the result in the same way. It works rather well even if the grouping method is very naive:

- For each allied ship not filtered out:
	- Iterate through all groups. If it is closer than 3 units away to one ship of that group, add it to that group, up to a maximum of 8.
	- If no group is found, create a new one with this ship.
- Eliminate all groups with only 1 ship.


# 2nd: FakePsyho

For a more detailed version, please take a look at [the link to FakePsyho's Post-Mortem](https://github.com/FakePsyho/halite2)


## General Guidance
- The golden rule is to **just focus on the things that have the biggest influence on your solution while keeping everything simple**.
- Avoid any metagame-specific problems (situations that occur exclusively due to currently dominating style of playing) and instead focus only on issues that after fixing them the outcome would be positive no matter how my opponents are behaving.
- Focused almost exclusively on 4-player games, because they had much higher impact on the final ranking

## Most Important Changes

- Use **global greedy strategy with evaluation function** for selecting destinations for ships (more on that below).
- Send correct number of ships to each planet (count ships already on the way)
- Limit amount of ships that can follow a single enemy ship.
- Primitive way of retreating when being outnumbered (called evasion in my code)
- In 4-player games, bump priority for planets furthest away from center, as well as drastically reduce priority for planets in the middle to avoid 3+ player battles.

## Phases

1. Pre-Process
  - This calculates various global/ship/planet features that are going to be used later.
2. Calculate Orders
  - This assigns high-level orders to each ship by using already-mentioned greedy assignment
3. Calculate Moves
  - Based on high-level orders, calculate move (i.e. angle/thrust pair) for each ship. **Moves are calculated using another evaluation function**. I iterate over all (angle, thrust) pairs, discard all moves that end up colliding and select the one that maximizes evaluation function. Depending on the type of move, evaluation function is called with different set of parameters that enable/disable various components of evaluation (distance to target, penalty from being close to enemies, bonus for being close to allies, etc.).
4. Evasion/Clustering Post-Process
  - Based on calculated moves, find all my ships that might fight inefficiently and recalculate moves for them. Fighting efficiency can be defined as ratio of my_expected_attacks / total_expected_attackss.
5. Baiting Post-Process
  - Based on calculated moves, try to find set of moves that may turn inefficient fight into efficient one.

## Core Concept: Evaluation Function

Basically, it's a function that **given some state/decision/situation will evaluate it to (usually) a single number. Allowing us to order states/decisions/situations from best to worst**. Designing solution around evaluation function means that you call your evaluation function with all potential choices and you select one that gives the best result. This means that if you want to give some type of decisions higher priority than to others, you need to bump up their values. If you have some machine learning experience, you can think of evaluation function as a model with high-level custom features and hand-crafted weights.

Evaluation function is generally used as a replacement for decision trees (random forest vs neural network analogy) or analytic solution. Good example of analytic vs evaluation is movement. You can try to calculate optimal move for ship directly (bad idea), or you can call your evaluation function for all possible angle/thrust values and select the best one. For example, the most naive pathfinding would be to evaluate all moves, for those that collide return -infinity and for those that don't collide return -distance_to_target. And that's already far superior to default navigation.

## Core Concept: Global Greedy Assignment

There's a common problem in AI-battle tasks where you have N units to your disposal and each of them can perform some set of actions. There's also a standard way of dealing with it. **If the evaluation of (unit, action) doesn't depend on results of other units, you can just iterate over all units and select the best action for each one.** If it depends, things get slightly more complicated. When your evaluation function is comparable between different units, you can use global greedy assignment (not an official name of algorithm, but it's quite descriptive).

```python
while (len(units_without_actions) > 0) {
  best_ship = null
  best_action = null
  best_eval = -infinity
  for unit in units_without_actions {
    for action in possible_actions {
      eval = evaluate(unit, action)
      if (eval > best_eval) {
        best_eval = eval
        best_unit = unit
        best_action = action
      }
    }
  }
  update(best_unit, best_action)
}
```

For most problems this is going to work really well and will give result close to perfect matching. The only downside is that the algorithm now takes O(ships^2\*actions) instead of O(ships\*actions). But well, just learn to write fast code ;) Since this loop was expensive for me, I **cached best action for each ship and recalculated it only when evaluation value for that action changed**. This works, because my evaluation function could not improve after update() equivalent. Which means, if action gave the same value, it's guaranteed that it's still the best choice. Small trick but slashed down execution times by 50-100x in worst cases for whole phase.

## Small Tricks

There are dozens of small tricks within the code. I'll give a list of some of the more interesting ones that I still remember:

- It wasn't mentioned anywhere, but my solution is completely **stateless** (other than knowing which turn it is). It drastically simplifies the solution and reduces the amount of possible bugs you can make. In general, unless you absolutely know what you're doing, keep your solution stateless.
- You may notice in my code that **both 3rd and 4th phases are performed several times**. 3rd phase has several passes because there's a chance that ship may want to go to a place which is currently occupied by another ship which may change after all ships are processed. Similarly 4th phase is repeated because it doesn't always happen that all ships will get marked to retreat in one pass. And, each time ship's move is recalculated, it affects the evaluation function values for neighboring ships.
- I use **expected spawning positions** of new ships during 4th phase and when evaluating movement. I just reimplemented the same function from Halite's source.
- Calculating if ship is for colonizing is a little bit tricky but I found a nice heuristic for that. Let us define "safe distance" as first distance where enemy ships outnumber our ships. This simulates the risk of getting outnumbered (and thus the miner dying defenceless).
- This was mentioned before, but limiting how many ships can follow each enemy ship is a really cheap way of forcing your units to spread among different goals. In fact, it works so well that I never got rid off this behavior.
- Normally when I'm targeting enemy ships, I'm using their previous position as my target (possibly adjusted by max speed so that I won't slow down when they were very close turn before). However, as a countermeasure for harassment. For single enemy units, I try to predict where the enemy would go by running my own move function on that unit and use the predicted movement as a new target.

### Ideas that haven't been implemented:

- I thought about **solving 3v3 rushes by using reinforced learning**. While the game is not a good target for ML/RL in general, since it essentially has two different logical layers (high-level order logic and low-level move logic). Those small-scale battles are ideal situation for them.
- Another random idea involving machine learning was to download all replays from top bots and train lstm-based supervised model for enemy ships as a predictive model. Then, use those predictions as expected moves and essentially modify our problem into optimization problem where each turn you try to maximize battle efficiency of our ships (damage dealt vs damage received). In the simplest form, I could try to use it for 3v3 battles only.
- There's somewhat easy way for implementing effective algorithm for selecting starting planets. It's very cheap to perform forward simulations of the game if you assume that ships are just going to the closest planet and all fights end up with both ships dead. This way you can perform hundreds of random simulations and take the one that gives highest expected ratio of your_ships / all_ships. Main reason why I haven't done this is that for 2-player games that would result in higher percentage of games ending up in rushes (my AI wasn't moving to the center as often as it should) so I wasn't sure if the net gain would be positive.

# 3rd: Shummie

For a more detailed version, please take a look at [the link to Shummie's Post-Mortem](https://shummie.github.io/Halite-2-Shummie/)

## Numeric Superiority

Basically, it boils down to: Do not fight in a fight where you cannot win. Prior to this, most ships just attacked each other haphazardly. But, in reality, fighting for a tie does nothing. Detecting if you were outnumbered, or in a tie, meant that you should try retreating back to a friendly ship to outnumber the opponent. By the end, every top bot was doing this in some form or fashion.

## **Non-Aggression Pact**

@ewirkerman and I had decided to collaborate and create a NAP in 4 player games. Every game, we would send a signal in 4p games, and if the secret handshake was detected, we would not attack each other’s docked ships. For all intents and purposes, our ships were invisible to each other (or… at least that was the intent). Also, we would make sure that the enemy was completely eliminated before turning on each other. This would, in theory, guarantee that we were placed 1st and 2nd when we were on the same side of the map, and in theory, would still have some benefit if we were across or diagonal from each other.

We kept it hidden until the final two hours of the competition. Surprisingly, no one noticed, and we saw a definite spike in our win rates when we were in the same game. We had done a lot of local testing to make sure we had all the bugs worked out. I even uploaded my alliance dance code for about 2 weeks, but if it detected a positive, i would immediately crash. This would give us an idea of how often our signal would have a false positive. In two weeks of playing, there were 0 false positives.

It wasn’t always that easy actually. Our original signal caused me to crash in about 30% of my 4p games. However, we found out later that @ewirkerman actually had been sending his signal the entire time! Despite that, I saw games where I was crashing where he wasn’t in it, so we decided to make our signal slightly more complicated so that we would reduce the frequency of false positives.

## Bot Logic Overview
A turn in my bot can be broken up into the following major steps which I’ll go into detail on:

- Turn Initialization
- Behavior/Target Assignment
- Target Post-Processing and Reassignment
- Navigation

### Behaviors: Distractor

The distractor bot was originally designed to be the “drone harass” bot. It was effective to send ships to docked ships and have it delay weaker bots from using new ships effectively and just use it to occupy 2-4 ships while trying to snipe off docked ships when possible.

As I talked about, the behaviors handle the strategic decisions, and the navigation handles the tactical function. My original navigation function for this role was the Attack_Docked_Ship_Avoid_All nav. That nav function basically always avoids getting into range of enemy undocked ships while trying to get into range of enemy docked ships. Eventually, I replaced this with what I call my dogfight nav function without changing the target selection of the distractor bot. Because of how I implemented the dogfight function, it still functions similarly to the old distractor bot behavior, but now if I have multiple distactors (or other combatants) nearby, it’ll know not to just try to avoid enemy ships if we have numeric advantage. This is how I get the “swarming” behavior where I target docked ships with a subset of ships and across the map instead of a single battlefront.

The 4-player version of this is almost identical, with the exception that we don’t want to target a docked ship that’s too far away from us since we should be focusing on the closest enemy.

### Navigation: Navigation Functions

- Default_Navigation
- Navigate_To_Planet
- Navigate_To_Planet_4p_Rush
- Retreat_From_All
- Defense
- Dogfight

### Navigation Evaluation

Here’s a summary of how we evaluate moves in this function

- Move toward target
- Calculate nearby_enemy
- Calculate nearby_friendly
- Aggression
- Rush mode handling
- Move to target
- Avoid Planets
- Aggressive scores
	- Bonus for distance traveled
	- Move toward closest enemy
	- Stay near friendly ships
	- Bonus for attacking multiple enemies
	- Bonus for docked enemy ships
	- Aggression bonus
- Non Aggressive Scores (less important than aggressive scores)
	- Bonus for distance traveled
	- Bonus for moving toward our target
	- Penalty for nearby_enemy_ships
	- Penalty for being in weapon range of an enemy
	- Stay near friendly ships
	- Kamakaze!

# References

References include:
[Post-Mortem Summary Page](https://2017.forums.halite.io/t/post-mortem-bot-source-code/1372),
[ReCurs3](https://recursive.cc/blog/halite-ii-post-mortem.html),
[FakePsyho](https://github.com/FakePsyho/halite2),
[Shummie](https://shummie.github.io/Halite-2-Shummie/)
