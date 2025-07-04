import logging
import os
from pathlib import Path

from cltl.brain.long_term_memory import LongTermMemory
from cltl.reply_generation.lenka_replier import LenkaReplier

import cltl.g2kmore.thought_util as util
from cltl.g2kmore.brain_g2kmore import BrainGetToKnowMore, ConvState

logger = logging.getLogger(__name__)


def fake_user_input(focus):
    triple = focus["triple"]

    ### We fill in a dummy as object to simulate new data for the eKG
    triple['object']['label'] = 'dummy'
    print('User: Triple as the fake user input: ', util.triple_to_string(triple))

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

    target = ("carl")
    type = "person"
    g2km.set_target(target, type)
    print("Set a goal for %s as a %s in state %s" % (target, type, g2km.state.name))

    while not g2km.state == ConvState.REACHED and not g2km.state == ConvState.GIVEUP:
        print('=======', g2km.state, '=======')
        # Reply is sometimes None as the replier randomly chooses between object and subject gaps
        response = g2km.evaluate_and_act()
        print('Nr of desires', len(g2km.desires))

        if not response:
            pass
        elif isinstance(response, str):
            print("Agent: ", response)
            print('User: Some user input as reply to', response)
        else:
            print("Agent: ", replier.reply_to_statement(response, thought_options=["_subject_gaps"]))

        # Wait for capsule event
        if g2km.state in [ConvState.QUERY]:
            capsule = fake_user_input(g2km.intention)
            brain.capsule_statement(capsule, reason_types=True, return_thoughts=True, create_label=True)

    print('Nr of desires', len(g2km.desires))
    print('g2km.state', g2km.state)
