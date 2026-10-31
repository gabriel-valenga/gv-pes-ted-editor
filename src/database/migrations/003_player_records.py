INTEGER_FIELDS = [
    "playerId",
    "callnameId",
    "countryId1",
    "height",
    "weight",
    "goalCelebration1",
    "goalCelebration2",
    "age",
    "isFromLiveUpdate",
    "isPlayerNameChanged",
    "unsafe_isDifferenceFromDefault",
    "attackingProwess",
    "ballControl",
    "weakFootUsage",
    "tightPossession",
    "lowPass",
    "loftedPass",
    "finishing",
    "placeKicking",
    "curl",
    "speed",
    "acceleration",
    "jump",
    "physicalContact",
    "balance",
    "stamina",
    "ballWinning",
    "aggression",
    "gkAwareness",
    "gkCatching",
    "form",
    "gkReach",
    "defensiveProwess",
    "gkClearing",
    "headingAbility",
    "dribbling",
    "injuryResistance",
    "attitude",
    "gkReflexes",
    "kickingPower",
    "weakFootAccuracy",
    "scissorsFeint",
    "doubleTouch",
    "flipFlap",
    "marseilleTurn",
    "sombrero",
    "crossOverTurn",
    "cutBehindAndTurn",
    "scotchMove",
    "stepOnSkillControl",
    "headingSkill",
    "longRangeDrive",
    "chipShotControl",
    "longRangeShooting",
    "knuckleShot",
    "dippingShot",
    "risingShot",
    "acrobaticFinishing",
    "heelTrick",
    "firstTimeShot",
    "oneTouchPass",
    "throughPassing",
    "weightedPass",
    "pinpointCrossing",
    "outsideCurler",
    "rabona",
    "noLookPass",
    "lowLoftedPass",
    "gkLowPunt",
    "gkHighPunt",
    "longThrow",
    "gkLongThrow",
    "penaltySpecialist",
    "gkPenaltySaver",
    "gamesmanship",
    "manMarking",
    "trackBack",
    "interception",
    "acrobaticClear",
    "captaincy",
    "superSub",
    "fightingSpirit",
    "trickster",
    "mazingRun",
    "speedingBullet",
    "incisiveRun",
    "longBallExpert",
    "earlyCross",
    "longRanger",
    "reputation",
    "dribHunch",
    "dribArmMove",
    "runHunch",
    "runArmMove",
    "dribMotion",
    "ckMotion",
    "fkMotion",
    "pkMotion",
]

BOOLEAN_FIELDS = [
    "isFromLiveUpdate",
    "isPlayerNameChanged",
    "unsafe_isDifferenceFromDefault",
    "scissorsFeint",
    "doubleTouch",
    "flipFlap",
    "marseilleTurn",
    "sombrero",
    "crossOverTurn",
    "cutBehindAndTurn",
    "scotchMove",
    "stepOnSkillControl",
    "headingSkill",
    "longRangeDrive",
    "chipShotControl",
    "longRangeShooting",
    "knuckleShot",
    "dippingShot",
    "risingShot",
    "acrobaticFinishing",
    "heelTrick",
    "firstTimeShot",
    "oneTouchPass",
    "throughPassing",
    "weightedPass",
    "pinpointCrossing",
    "outsideCurler",
    "rabona",
    "noLookPass",
    "lowLoftedPass",
    "gkLowPunt",
    "gkHighPunt",
    "longThrow",
    "gkLongThrow",
    "penaltySpecialist",
    "gkPenaltySaver",
    "gamesmanship",
    "manMarking",
    "trackBack",
    "interception",
    "acrobaticClear",
    "captaincy",
    "superSub",
    "fightingSpirit",
    "trickster",
    "mazingRun",
    "speedingBullet",
    "incisiveRun",
    "longBallExpert",
    "earlyCross",
    "longRanger",
]

TEXT_FIELDS = [
    "playerName",
    "clubShirtName",
    "ntShirtName",
    "strongerFoot",
    "strongerHand",
    "registeredPosition",
    "positionGk",
    "positionCb",
    "positionLb",
    "positionRb",
    "positionDmf",
    "positionCmf",
    "positionLmf",
    "positionRmf",
    "positionAmf",
    "positionRwf",
    "positionLwf",
    "positionSs",
    "positionCf",
    "playingStyle",
]


def upgrade(connection):
    """Create the player records table."""
    columns = [
        (
            f"{field} INTEGER CHECK ({field} IN (0, 1))"
            if field in BOOLEAN_FIELDS
            else f"{field} INTEGER"
        )
        for field in INTEGER_FIELDS
    ]

    columns.extend(
        f"{field} TEXT"
        for field in TEXT_FIELDS
    )

    columns.append("""
        playerAppearance BLOB
        CHECK (
            playerAppearance IS NULL
            OR length(playerAppearance) = 72
        )
    """)

    columns.extend([
        "ted_file_id INTEGER NOT NULL",
        "player_index INTEGER NOT NULL",
        "FOREIGN KEY (ted_file_id) "
        "REFERENCES ted_files(id) ON DELETE RESTRICT",
        "UNIQUE (ted_file_id, player_index)",
    ])

    connection.execute(
        f"""
        CREATE TABLE player_records (
            id INTEGER PRIMARY KEY,
            {", ".join(columns)}
        )
        """
    )

    connection.execute("""
        CREATE INDEX idx_player_records_player_id
        ON player_records(playerId)
    """)