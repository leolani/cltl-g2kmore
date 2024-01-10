import logging
import os
from pathlib import Path

from cltl.brain.long_term_memory import LongTermMemory
from cltl.reply_generation.lenka_replier import LenkaReplier

import thought_util as util
from cltl.g2kmore.brain_g2kmore import BrainGetToKnowMore, ConvState

logger = logging.getLogger(__name__)


def fake_user_input(focus):
    triple = focus["triple"]

    ### for some reason hyphens are lost in de predicates, hack to repair this
    triple["predicate"]['label'] = triple["predicate"]['label'].replace(" ", "-")
    triple["predicate"]['uri'] = triple["predicate"]['uri'].replace(" ", "-")
    ### We fill in a dummy as object to simulate new data for the eKG
    triple['object']['label'] = 'dummy'
    print('Triple as the fake user input: ', util.triple_to_string(triple))

    return util.make_capsule_from_triple(triple)


def test_brain():
    # testing the brain:
    context = util.make_context()
    response = brain.capsule_context(context)
    print("response pushing context", response)

    capsule = util.make_capsule_from_triple()
    response = brain.capsule_statement(capsule, reason_types=True, return_thoughts=True, create_label=False)
    print("response pushing statement", response)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s.%(msecs)03d %(levelname)s %(module)s - %(funcName)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    log_path = "log_path"
    if not os.path.exists(log_path):
        dir = os.mkdir(log_path)
    brain = LongTermMemory(address="http://localhost:7200/repositories/sandbox",
                           log_dir=Path(log_path), clear_all=False)
    # test_brain()

    replier = LenkaReplier()
    g2km = BrainGetToKnowMore(brain, max_attempts=10, max_intention_attempts=3)

    target = "franziska"
    type = "person"
    brain_response = brain.capsule_mention(util.make_target(target, type),
                                           reason_types=True, return_thoughts=True, create_label=False)

    g2km.set_desires(brain_response)
    print("Set a goal for %s as a %s in state %s" % (target, type, g2km.state.name))

    while not g2km.state == ConvState.REACHED and not g2km.state == ConvState.GIVEUP:
        print('=======', g2km.state, '=======')
        thought = g2km.get_action()
        if not thought:
            pass
        elif isinstance(thought, str):
            print("Reply: ", thought)
            print('Some user input as reply to', thought)
        else:
            # Reply is sometimes None as the replier randomly chooses between object and subject gaps
            print("Thought: ", thought)
            print("Reply: ", replier.reply_to_statement(thought, thought_options=["_subject_gaps"]))
            capsule = fake_user_input(g2km.intention)
            g2km.add_knowledge(capsule)
