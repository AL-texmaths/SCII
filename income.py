# ================================================================
# SC2 INCOME EXTRACTOR
# Compatible avec :
#
#   PySC2 4.0.0
#   StarCraft II 5.0.16.97563
#   Python 3.12
#
# Méthode utilisée :
#
#   run_config.start()
#   controller.replay_info()
#   controller.start_replay()
#   controller.observe()
#   controller.step()
#
# ================================================================


# ================================================================
# CONFIGURATION SC2
# ================================================================

import os

SC2PATH = r"D:\StarCraft II"

# IMPORTANT :
# Doit être défini AVANT run_configs.get().

os.environ["SC2PATH"] = SC2PATH


# ================================================================
# IMPORTS
# ================================================================

from pathlib import Path
from tkinter import Tk, filedialog

import numpy as np
import matplotlib.pyplot as plt

from absl import flags

from pysc2 import run_configs
from s2clientprotocol import sc2api_pb2 as sc_pb


# ================================================================
# CONFIGURATION
# ================================================================

# Nombre de game loops entre deux observations.
#
# SC2 fonctionne à environ 22.4 game loops / seconde.
#
# 16 loops :
#
#     16 / 22.4 = 0.714 seconde
#
# soit environ 1.4 observations / seconde.
#
# Une fois que tout fonctionne, tu peux passer à 1 pour
# obtenir la résolution maximale.

STEP_MUL = 16


# Joueur à analyser.
#
# Ton replay de test contient :
#
#   player_id = 1 : ZiptoV
#   player_id = 2 : IA
#
PLAYER_ID = 1


# Fichier de sortie.

OUTPUT_FILE = "sc2_income.npz"


# ================================================================
# SÉLECTION DU REPLAY
# ================================================================

def select_replay():
    """
    Ouvre une fenêtre Windows permettant de sélectionner
    un fichier .SC2Replay.
    """

    root = Tk()

    root.withdraw()

    path = filedialog.askopenfilename(
        title="Sélectionner un replay StarCraft II",

        filetypes=[
            (
                "StarCraft II Replay",
                "*.SC2Replay",
            ),
            (
                "Tous les fichiers",
                "*.*",
            ),
        ],
    )

    root.destroy()

    if not path:

        raise RuntimeError(
            "Aucun replay sélectionné."
        )

    return Path(path).resolve()


# ================================================================
# EXTRACTION
# ================================================================

def extract_income(replay_path):
    """
    Lance StarCraft II directement via PySC2,
    charge le replay et extrait les données économiques.

    Les données sont récupérées depuis :

        response.observation.score.score_details

    notamment :

        collection_rate_minerals
        collection_rate_vespene
        collected_minerals
        collected_vespene

    Returns
    -------
    game_loops : np.ndarray

    time : np.ndarray

    minerals_rate : np.ndarray

    gas_rate : np.ndarray

    collected_minerals : np.ndarray

    collected_gas : np.ndarray
    """

    # ============================================================
    # VALIDATION DU REPLAY
    # ============================================================

    replay_path = Path(
        replay_path
    ).resolve()

    if not replay_path.is_file():

        raise FileNotFoundError(
            f"Replay introuvable : {replay_path}"
        )


    # ============================================================
    # INFORMATIONS
    # ============================================================

    print()

    print(
        "=" * 70
    )

    print(
        "STARCRAFT II - EXTRACTION DU REVENU"
    )

    print(
        "=" * 70
    )

    print(
        "SC2PATH :",
        SC2PATH,
    )

    print(
        "Replay  :",
        replay_path,
    )

    print(
        "Existe  :",
        replay_path.is_file(),
    )

    print(
        "STEP_MUL:",
        STEP_MUL,
    )

    print()


    # ============================================================
    # RUN CONFIG
    # ============================================================

    # IMPORTANT :
    #
    # On utilise exactement la méthode qui fonctionne
    # dans ton test_replay.py.
    #
    # Il ne faut PAS faire :
    #
    #     run_configs.get("windows")
    #
    # ni :
    #
    #     run_config="windows"
    #
    # Chez toi, run_configs.get() détecte correctement
    # le run config Windows.

    run_config = run_configs.get()

    print(
        "Run config :",
        run_config,
    )

    print(
        "Version    :",
        run_config.version,
    )

    print()


    # ============================================================
    # PROCESSUS SC2
    # ============================================================

    process = None


    # ============================================================
    # TABLEAUX DE DONNÉES
    # ============================================================

    game_loops = []

    minerals_rate = []

    gas_rate = []

    collected_minerals = []

    collected_gas = []


    try:

        # ========================================================
        # LANCEMENT DE STARCRAFT II
        # ========================================================

        print(
            "Lancement du processus SC2..."
        )

        process = run_config.start(
            want_rgb=False,
        )

        controller = process.controller

        print(
            "Processus SC2 lancé."
        )

        print(
            "Controller :",
            type(controller).__name__,
        )

        print()


        # ========================================================
        # LECTURE DU FICHIER REPLAY
        # ========================================================

        with open(
            replay_path,
            "rb",
        ) as f:

            replay_data = f.read()


        print(
            "Taille du replay :",
            len(replay_data),
            "octets",
        )

        print()


        # ========================================================
        # INFORMATIONS DU REPLAY
        # ========================================================

        print(
            "Lecture des informations du replay..."
        )

        replay_info = controller.replay_info(
            replay_data
        )

        print(
            "Replay info récupéré !"
        )

        print(
            "Map :",
            replay_info.map_name,
        )

        print(
            "Version :",
            replay_info.game_version,
        )

        print(
            "Durée :",
            f"{replay_info.game_duration_seconds:.2f} s",
        )

        print(
            "Game loops :",
            replay_info.game_duration_loops,
        )

        print()


        # ========================================================
        # OPTIONS DE L'INTERFACE
        # ========================================================

        interface = sc_pb.InterfaceOptions(
            raw=True,
            score=True,
        )


        # ========================================================
        # DÉMARRAGE DU REPLAY
        # ========================================================

        print(
            "Démarrage du replay..."
        )

        controller.start_replay(
            sc_pb.RequestStartReplay(

                replay_data=replay_data,

                observed_player_id=PLAYER_ID,

                disable_fog=True,

                options=interface,
            )
        )

        print(
            "Replay démarré !"
        )

        print()


        # ========================================================
        # EXTRACTION
        # ========================================================

        print(
            "Extraction des données économiques..."
        )

        print()


        observation_count = 0


        while True:

            # ====================================================
            # OBSERVATION
            # ====================================================

            response = controller.observe()

            observation = response.observation


            # ====================================================
            # GAME LOOP
            # ====================================================

            loop = observation.game_loop


            # ====================================================
            # SCORE
            # ====================================================

            # IMPORTANT :
            #
            # response est un :
            #
            #     ResponseObservation
            #
            # response.observation est un :
            #
            #     Observation
            #
            # et Observation contient :
            #
            #     score
            #
            # Le score économique est ensuite dans :
            #
            #     score.score_details
            #

            score = observation.score

            score_details = (
                score.score_details
            )


            # ====================================================
            # REVENU MINERAI
            # ====================================================

            mineral_income = (
                score_details.collection_rate_minerals
            )


            # ====================================================
            # REVENU GAZ
            # ====================================================

            gas_income = (
                score_details.collection_rate_vespene
            )


            # ====================================================
            # MINERAI TOTAL COLLECTÉ
            # ====================================================

            mineral_total = (
                score_details.collected_minerals
            )


            # ====================================================
            # GAZ TOTAL COLLECTÉ
            # ====================================================

            gas_total = (
                score_details.collected_vespene
            )


            # ====================================================
            # STOCKAGE
            # ====================================================

            game_loops.append(
                loop
            )

            minerals_rate.append(
                mineral_income
            )

            gas_rate.append(
                gas_income
            )

            collected_minerals.append(
                mineral_total
            )

            collected_gas.append(
                gas_total
            )


            observation_count += 1


            # ====================================================
            # AFFICHAGE
            # ====================================================

            if (
                observation_count == 1
                or observation_count % 100 == 0
            ):

                time_seconds = (
                    loop / 22.4
                )

                print(
                    f"Observations : "
                    f"{observation_count:6d} | "
                    f"loop={loop:6d} | "
                    f"temps={time_seconds:8.2f}s | "
                    f"minerai/min={mineral_income:7.1f} | "
                    f"gaz/min={gas_income:7.1f}"
                )


            # ====================================================
            # FIN DU REPLAY
            # ====================================================

            # Premier indicateur :
            #
            # SC2 fournit le résultat du joueur.

            if response.player_result:

                print()

                print(
                    "Résultat du joueur détecté."
                )

                break


            # Deuxième sécurité :
            #
            # on connaît déjà la durée du replay.

            if (
                loop
                >= replay_info.game_duration_loops
            ):

                print()

                print(
                    "Fin du replay atteinte."
                )

                break


            # ====================================================
            # AVANCER LE REPLAY
            # ====================================================

            controller.step(
                STEP_MUL
            )


        # ========================================================
        # FIN EXTRACTION
        # ========================================================

        print()

        print(
            "Extraction terminée."
        )

        print(
            "Nombre d'observations :",
            observation_count,
        )


    finally:

        # ========================================================
        # FERMETURE SC2
        # ========================================================

        if process is not None:

            print()

            print(
                "Fermeture propre de SC2..."
            )

            process.close()

            print(
                "SC2 fermé."
            )


    # ============================================================
    # CONVERSION NUMPY
    # ============================================================

    game_loops = np.asarray(
        game_loops,
        dtype=np.int64,
    )

    minerals_rate = np.asarray(
        minerals_rate,
        dtype=np.float64,
    )

    gas_rate = np.asarray(
        gas_rate,
        dtype=np.float64,
    )

    collected_minerals = np.asarray(
        collected_minerals,
        dtype=np.float64,
    )

    collected_gas = np.asarray(
        collected_gas,
        dtype=np.float64,
    )


    # ============================================================
    # TEMPS
    # ============================================================

    # SC2 tourne à environ 22.4 game loops/seconde.

    time = (
        game_loops / 22.4
    )


    # ============================================================
    # RETOUR
    # ============================================================

    return (
        game_loops,
        time,
        minerals_rate,
        gas_rate,
        collected_minerals,
        collected_gas,
    )


# ================================================================
# SAUVEGARDE
# ================================================================

def save_data(
    filename,
    game_loops,
    time,
    minerals_rate,
    gas_rate,
    collected_minerals,
    collected_gas,
):

    np.savez(
        filename,

        game_loops=game_loops,

        time=time,

        minerals_rate=minerals_rate,

        gas_rate=gas_rate,

        collected_minerals=collected_minerals,

        collected_gas=collected_gas,
    )

    print()

    print(
        f"Données sauvegardées dans : {filename}"
    )


# ================================================================
# GRAPHIQUE
# ================================================================

def plot_income(
    time,
    minerals_rate,
    gas_rate,
):

    if len(time) == 0:

        print(
            "Impossible de créer le graphique : "
            "aucune donnée."
        )

        return


    # ------------------------------------------------------------
    # Conversion secondes -> minutes
    # ------------------------------------------------------------

    time_minutes = (
        time / 60.0
    )


    # ------------------------------------------------------------
    # Figure
    # ------------------------------------------------------------

    fig, ax = plt.subplots(
        figsize=(12, 6)
    )


    # ------------------------------------------------------------
    # Minerai
    # ------------------------------------------------------------

    ax.plot(
        time_minutes,

        minerals_rate,

        color="goldenrod",

        linewidth=1.2,

        label="Minerai / min",
    )


    # ------------------------------------------------------------
    # Gaz
    # ------------------------------------------------------------

    ax.plot(
        time_minutes,

        gas_rate,

        color="green",

        linewidth=1.2,

        label="Gaz / min",
    )


    # ------------------------------------------------------------
    # Axes
    # ------------------------------------------------------------

    ax.set_xlabel(
        "Temps (minutes)"
    )

    ax.set_ylabel(
        "Rendement (ressources/min)"
    )


    # ------------------------------------------------------------
    # Titre
    # ------------------------------------------------------------

    ax.set_title(
        "Rendement économique SC2"
    )


    # ------------------------------------------------------------
    # Grille
    # ------------------------------------------------------------

    ax.grid(
        True,

        alpha=0.3,

        linestyle="--",
    )


    # ------------------------------------------------------------
    # Légende
    # ------------------------------------------------------------

    ax.legend()


    # ------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------

    plt.tight_layout()


    # ------------------------------------------------------------
    # Affichage
    # ------------------------------------------------------------

    plt.show()


# ================================================================
# MAIN
# ================================================================

def main():

    # ============================================================
    # SÉLECTION DU REPLAY
    # ============================================================

    replay_path = select_replay()


    # ============================================================
    # EXTRACTION
    # ============================================================

    (
        game_loops,

        time,

        minerals_rate,

        gas_rate,

        collected_minerals,

        collected_gas,

    ) = extract_income(
        replay_path
    )


    # ============================================================
    # VÉRIFICATION
    # ============================================================

    if len(game_loops) == 0:

        print()

        print(
            "Aucune observation n'a été récupérée."
        )

        return


    # ============================================================
    # RÉSULTATS
    # ============================================================

    print()

    print(
        "=" * 70
    )

    print(
        "RÉSULTATS"
    )

    print(
        "=" * 70
    )


    print(
        "Nombre d'observations :",
        len(game_loops),
    )

    print(
        "Premier game loop     :",
        game_loops[0],
    )

    print(
        "Dernier game loop     :",
        game_loops[-1],
    )

    print(
        "Durée                 :",
        f"{time[-1]:.2f} s",
    )


    if len(time) > 1:

        mean_resolution = (
            np.mean(
                np.diff(time)
            )
        )

        print(
            "Résolution moyenne    :",
            f"{mean_resolution:.5f} s",
        )


    # ============================================================
    # PREMIERS ÉCHANTILLONS
    # ============================================================

    print()

    print(
        "Premiers échantillons :"
    )

    print()


    for i in range(
        min(20, len(time))
    ):

        print(
            f"loop={game_loops[i]:6d} | "
            f"t={time[i]:8.3f}s | "
            f"minerai/min={minerals_rate[i]:7.1f} | "
            f"gaz/min={gas_rate[i]:7.1f} | "
            f"minerai total={collected_minerals[i]:7.1f} | "
            f"gaz total={collected_gas[i]:7.1f}"
        )


    # ============================================================
    # DERNIÈRE VALEUR
    # ============================================================

    print()

    print(
        "Dernière observation :"
    )

    print()

    print(
        f"loop={game_loops[-1]:6d} | "
        f"t={time[-1]:8.3f}s | "
        f"minerai/min={minerals_rate[-1]:7.1f} | "
        f"gaz/min={gas_rate[-1]:7.1f} | "
        f"minerai total={collected_minerals[-1]:7.1f} | "
        f"gaz total={collected_gas[-1]:7.1f}"
    )


    # ============================================================
    # SAUVEGARDE
    # ============================================================

    save_data(

        OUTPUT_FILE,

        game_loops,

        time,

        minerals_rate,

        gas_rate,

        collected_minerals,

        collected_gas,
    )


    # ============================================================
    # GRAPHIQUE
    # ============================================================

    plot_income(

        time,

        minerals_rate,

        gas_rate,
    )


# ================================================================
# ENTRY POINT
# ================================================================

if __name__ == "__main__":

    # ============================================================
    # IMPORTANT :
    #
    # run_configs.get() utilise des flags absl.
    #
    # Sans parsing :
    #
    #     UnparsedFlagAccessError
    #
    # apparaît.
    #
    # Cette ligne est donc volontaire et vient directement
    # de la solution validée dans test_replay.py.
    # ============================================================

    flags.FLAGS(
        ["income.py"]
    )

    main()
