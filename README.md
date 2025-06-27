# cltl-g2kmore

This application uses an episodic Knowledge Graph (eKG) to drive the communication with a user to learn about his/her Activities of Daily Life (ADL), such as eating, cooking, visiting friends, watching movies, sleeping, etc.
To achieve this it queries the eKG for all activities already stored and asks questions to fill any gaps between the current interaction and the last interaction, basically asking what you have been up to lately.
See our reference for further explanations and motivation.

Higher order **INTENT** model following a Belief-Desire-Intent model. The goal of this model is to get more knowledgeable about a topic of a certain type, about you as a person or Amsterdam as a city.
The module proceeds according to the following steps, defined in _take_action(target, type):

1. _define(target, type): defines the goals
2.  _evaluate(): evaluate the status of the goal:
3. While the _state is not REACHED or GIVEUP, do:
   1. _pursue
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

## Examples

In the examples folder you find some scripts to demonstrate the application:

* structured_diary/generate_events.py
* structured_diary/structured_diary.py
* structured_diary/visualise_timeline.py
* get_temporal_containers.py
* achieve_goal.py

The application has some helper functions to preload a history of events in the eKG, which can either be loaded from a JSON file
or generated randomly. For the latter, you can specify the list of people, places and activities from which it draws random combinations centered around the name of the user.

Furthermore, it has a function to visualise the eKG history on a timeline for a given period. 

## Requirements
The application was created in Python 3.9. The dependencies are defined in the requirements.txt file. To get started:

1. create a virtual environment with Python 3.9 and activate the environment
2. run pip install -r requirements.txt from the command line with the environment active
3. Download and install [GraphDB](https://www.ontotext.com/products/graphdb) on your local computer
4. Define a new repository in GraphDB with the name "demo" which will act as the episodic Knowledge Graph

##

## Events

## Reference
P. Vossen, S. Báez Santamaría, and T. Baier, “A conversational agent for structured diary construction enabling monitoring of functioning & well-being,” in Hhai 2024: hybrid human ai systems for the social good, IOS Press, 2024, p. 315–324.
[BibTeX]
@incollection{vossen2024conversational,
title={A Conversational Agent for Structured Diary Construction Enabling Monitoring of Functioning \& Well-Being},
author={Vossen, Piek and B{\'a}ez Santamar{\'\i}a, Selene and Baier, Thomas},
booktitle={HHAI 2024: Hybrid Human AI Systems for the Social Good},
pages={315--324},
year={2024},
publisher={IOS Press}
}

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
