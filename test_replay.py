import os
import time

from pysc2 import run_configs
from pysc2.lib import protocol
from s2clientprotocol import sc2api_pb2 as sc_pb
from absl import flags



SC2PATH = r"D:\StarCraft II"
REPLAY = os.path.abspath(r"replays\4base_macro_1.SC2Replay")


def main():
    print("=" * 70)
    print("TEST REPLAY")
    print("=" * 70)

    os.environ["SC2PATH"] = SC2PATH

    print("SC2PATH :", os.environ["SC2PATH"])
    print("Replay  :", REPLAY)
    print("Existe  :", os.path.isfile(REPLAY))
    print()

    run_config = run_configs.get()
    print("Run config :", run_config)
    print("Version    :", run_config.version)
    print()

    process = None

    try:
        print("Lancement du processus SC2...")

        process = run_config.start(
            want_rgb=False,
        )

        controller = process.controller

        print("Processus SC2 lancé.")
        print("Controller :", type(controller).__name__)
        print()

        with open(REPLAY, "rb") as f:
            replay_data = f.read()

        print("Taille du replay :", len(replay_data), "octets")
        print()

        # ------------------------------------------------------------
        # Informations du replay
        # ------------------------------------------------------------

        print("Lecture des informations du replay...")

        replay_info = controller.replay_info(replay_data)

        print("Replay info récupéré !")
        print(replay_info)
        print()

        # ------------------------------------------------------------
        # Lancement du replay
        # ------------------------------------------------------------

        print("Démarrage du replay...")

        interface = sc_pb.InterfaceOptions(
            raw=True,
            score=True,
        )

        controller.start_replay(
            sc_pb.RequestStartReplay(
                replay_data=replay_data,
                observed_player_id=1,
                disable_fog=True,
                options=interface,
            )
        )


        print("Replay démarré !")
        print()

        # ------------------------------------------------------------
        # Récupération de quelques observations
        # ------------------------------------------------------------

        print("Récupération des observations...")

        for i in range(10):
            obs = controller.observe()

            print(obs.observation.score)
            print(type(obs.observation.score))
            print(dir(obs.observation.score))

            print(
                f"Observation {i + 1}: "
                f"game_loop={obs.observation.game_loop}"
            )

            if obs.player_result:
                print("Résultat du joueur :", obs.player_result)

            if obs.observation.game_loop > 0:
                pass

            # Faire avancer le replay.
            controller.step(16)

        print()
        print("TEST REPLAY RÉUSSI !")

    except Exception as e:
        print()
        print("=" * 70)
        print("ERREUR")
        print("=" * 70)
        print(type(e).__name__, ":", e)
        raise

    finally:
        if process is not None:
            print()
            print("Fermeture propre de SC2...")
            process.close()
            print("SC2 fermé.")


if __name__ == "__main__":
    flags.FLAGS(["test_replay.py"])
    main()

