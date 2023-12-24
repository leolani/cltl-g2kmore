# cltl-g2kmore

Higher order **INTENT** model following a Belief-Desire-Intent model. The goal of this model is to get more knowledgeable about a topic of a certain type, aboit you as a person or Amsterdam as a city.
The module proceeds according to the following steps, defined in _take_action(target, type):

1. _define(target, type): defines the goals
2.  _evaluate(): evaluate the status of the goal:
3. While the _state is not REACHED or GIVEUP, do:
   1. _pursui
   2. _wait
   3. _evaluate()
4. When done, _repond() the result

For the g2kmore module, goals are defined as knowledge gaps about the Target topic which is a Type. 
The Target and the Type should be known, otherwise no goal can be set. Types are predefined in the N2MU ontology.
Targets needs to be added to the graph by communicating about an instance of a Type to populate the graph with it.
The most basic way is to introduce yourself to the agent or talk about somebody/something else. 
Given the Type, the agent will generate things it could possibly know about the Target but does not. 
These represent the gaps of knowledge to be filled.

When evaluating, we check if all goals have been reached or we exceeded the threshold of reaching the goals (_goal_attempts_max).
One subgoal will be in focus and is tried for a maximum number of times (_focus_attempt_max)
The evaluation function:

1. Checks if all gaps are filled or the number of attempts exceeded a threshold (__goal_attempts_max)
2. If not it randomly selects a gap as the _focus or continues with the current _focus unless it exceeds a threshold (_focus_attempt_max)


This repository is a component of the [Leolani framework](https://github.com/leolani/cltl-combot).
For usage of the component within the framework see the instructions there.


## Contributing

Contributions are what make the open source community such an amazing place to be learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


<!-- LICENSE -->
## License

Distributed under the MIT License. See [`LICENSE`](https://github.com/leolani/cltl-combot/blob/main/LICENCE) for more information.

<!-- CONTACT -->
## Authors

* [Thomas Baier](https://www.linkedin.com/in/thomas-baier-05519030/)
* [Selene Báez Santamaría](https://selbaez.github.io/)
* [Piek Vossen](https://github.com/piekvossen)