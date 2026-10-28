POS_ORDER = ["GK", "CB", "LB", "RB", "DMF", "CMF", "LMF", "RMF", "AMF", "LWF", "RWF", "SS", "CF"]

PLAYER_FIELDS = [
    {
        "key": "playerId",
        "startByte": 0,
        "length": 4,
        "type": "bytes"
    },
    {
        "key": "callnameId",
        "startByte": 4,
        "length": 4,
        "type": "bytes"
    },
    {
        "key": "playerName",
        "startByte": 54,
        "length": 61,
        "type": "string"
    },
    {
        "key": "clubShirtName",
        "startByte": 115,
        "length": 61,
        "type": "string"
    },
    {
        "key": "ntShirtName",
        "startByte": 176,
        "length": 61,
        "type": "string"
    },
    {
        "key": "countryId1",
        "startByte": 8,
        "length": 2,
        "type": "bytes"
    },
    {
        "key": "height",
        "startByte": 10,
        "length": 1,
        "type": "bytes"
    },
    {
        "key": "weight",
        "startByte": 11,
        "length": 1,
        "type": "bytes"
    },
    {
        "key": "goalCelebration1",
        "startByte": 12,
        "length": 1,
        "type": "bytes"
    },
    {
        "key": "goalCelebration2",
        "startByte": 13,
        "length": 1,
        "type": "bytes"
    },
    {
        "key": "age",
        "startByte": 32,
        "startBit": 7,
        "lengthInBit": 6,
        "type": "bitfield"
    },
    {
        "key": "isFromLiveUpdate",
        "startByte": 44,
        "startBit": 28,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "strongerFoot",
        "startByte": 44,
        "startBit": 29,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "l4"
    },
    {
        "key": "strongerHand",
        "startByte": 44,
        "startBit": 30,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "l4"
    },
    {
        "key": "isPlayerNameChanged",
        "startByte": 28,
        "startBit": 31,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "unsafe_isDifferenceFromDefault",
        "startByte": 44,
        "startBit": 22,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "registeredPosition",
        "startByte": 32,
        "startBit": 13,
        "lengthInBit": 4,
        "type": "bitfield",
        "transform": "eB"
    },
    {
        "key": "positionGk",
        "startByte": 40,
        "startBit": 13,
        "lengthInBit": 2,
        "type": "bitfield",
        "transform": "dt"
    },
    {
        "key": "positionCb",
        "startByte": 40,
        "startBit": 15,
        "lengthInBit": 2,
        "type": "bitfield",
        "transform": "dt"
    },
    {
        "key": "positionLb",
        "startByte": 40,
        "startBit": 17,
        "lengthInBit": 2,
        "type": "bitfield",
        "transform": "dt"
    },
    {
        "key": "positionRb",
        "startByte": 40,
        "startBit": 19,
        "lengthInBit": 2,
        "type": "bitfield",
        "transform": "dt"
    },
    {
        "key": "positionDmf",
        "startByte": 40,
        "startBit": 21,
        "lengthInBit": 2,
        "type": "bitfield",
        "transform": "dt"
    },
    {
        "key": "positionCmf",
        "startByte": 40,
        "startBit": 23,
        "lengthInBit": 2,
        "type": "bitfield",
        "transform": "dt"
    },
    {
        "key": "positionLmf",
        "startByte": 40,
        "startBit": 25,
        "lengthInBit": 2,
        "type": "bitfield",
        "transform": "dt"
    },
    {
        "key": "positionRmf",
        "startByte": 40,
        "startBit": 27,
        "lengthInBit": 2,
        "type": "bitfield",
        "transform": "dt"
    },
    {
        "key": "positionAmf",
        "startByte": 40,
        "startBit": 29,
        "lengthInBit": 2,
        "type": "bitfield",
        "transform": "dt"
    },
    {
        "key": "positionRwf",
        "startByte": 44,
        "startBit": 0,
        "lengthInBit": 2,
        "type": "bitfield",
        "transform": "dt"
    },
    {
        "key": "positionLwf",
        "startByte": 44,
        "startBit": 20,
        "lengthInBit": 2,
        "type": "bitfield",
        "transform": "dt"
    },
    {
        "key": "positionSs",
        "startByte": 44,
        "startBit": 2,
        "lengthInBit": 2,
        "type": "bitfield",
        "transform": "dt"
    },
    {
        "key": "positionCf",
        "startByte": 44,
        "startBit": 4,
        "lengthInBit": 2,
        "type": "bitfield",
        "transform": "dt"
    },
    {
        "key": "attackingProwess",
        "startByte": 12,
        "startBit": 16,
        "lengthInBit": 7,
        "type": "bitfield"
    },
    {
        "key": "ballControl",
        "startByte": 12,
        "startBit": 23,
        "lengthInBit": 7,
        "type": "bitfield"
    },
    {
        "key": "weakFootUsage",
        "startByte": 12,
        "startBit": 30,
        "lengthInBit": 2,
        "type": "bitfield",
        "transform": "P1"
    },
    {
        "key": "tightPossession",
        "startByte": 16,
        "startBit": 0,
        "lengthInBit": 7,
        "type": "bitfield"
    },
    {
        "key": "lowPass",
        "startByte": 16,
        "startBit": 7,
        "lengthInBit": 7,
        "type": "bitfield"
    },
    {
        "key": "loftedPass",
        "startByte": 16,
        "startBit": 14,
        "lengthInBit": 7,
        "type": "bitfield"
    },
    {
        "key": "finishing",
        "startByte": 16,
        "startBit": 21,
        "lengthInBit": 7,
        "type": "bitfield"
    },
    {
        "key": "placeKicking",
        "startByte": 20,
        "startBit": 0,
        "lengthInBit": 7,
        "type": "bitfield"
    },
    {
        "key": "curl",
        "startByte": 20,
        "startBit": 7,
        "lengthInBit": 7,
        "type": "bitfield"
    },
    {
        "key": "speed",
        "startByte": 20,
        "startBit": 14,
        "lengthInBit": 7,
        "type": "bitfield"
    },
    {
        "key": "acceleration",
        "startByte": 20,
        "startBit": 21,
        "lengthInBit": 7,
        "type": "bitfield"
    },
    {
        "key": "jump",
        "startByte": 24,
        "startBit": 0,
        "lengthInBit": 7,
        "type": "bitfield"
    },
    {
        "key": "physicalContact",
        "startByte": 24,
        "startBit": 7,
        "lengthInBit": 7,
        "type": "bitfield"
    },
    {
        "key": "balance",
        "startByte": 24,
        "startBit": 14,
        "lengthInBit": 7,
        "type": "bitfield"
    },
    {
        "key": "stamina",
        "startByte": 24,
        "startBit": 21,
        "lengthInBit": 7,
        "type": "bitfield"
    },
    {
        "key": "ballWinning",
        "startByte": 28,
        "startBit": 0,
        "lengthInBit": 7,
        "type": "bitfield"
    },
    {
        "key": "aggression",
        "startByte": 28,
        "startBit": 7,
        "lengthInBit": 7,
        "type": "bitfield"
    },
    {
        "key": "gkAwareness",
        "startByte": 28,
        "startBit": 14,
        "lengthInBit": 7,
        "type": "bitfield"
    },
    {
        "key": "gkCatching",
        "startByte": 28,
        "startBit": 21,
        "lengthInBit": 7,
        "type": "bitfield"
    },
    {
        "key": "form",
        "startByte": 28,
        "startBit": 28,
        "lengthInBit": 3,
        "type": "bitfield",
        "transform": "P1"
    },
    {
        "key": "gkReach",
        "startByte": 32,
        "startBit": 0,
        "lengthInBit": 7,
        "type": "bitfield"
    },
    {
        "key": "defensiveProwess",
        "startByte": 36,
        "startBit": 0,
        "lengthInBit": 7,
        "type": "bitfield"
    },
    {
        "key": "gkClearing",
        "startByte": 36,
        "startBit": 7,
        "lengthInBit": 7,
        "type": "bitfield"
    },
    {
        "key": "headingAbility",
        "startByte": 36,
        "startBit": 14,
        "lengthInBit": 7,
        "type": "bitfield"
    },
    {
        "key": "dribbling",
        "startByte": 40,
        "startBit": 0,
        "lengthInBit": 7,
        "type": "bitfield"
    },
    {
        "key": "injuryResistance",
        "startByte": 40,
        "startBit": 7,
        "lengthInBit": 2,
        "type": "bitfield",
        "transform": "P1"
    },
    {
        "key": "attitude",
        "startByte": 40,
        "startBit": 9,
        "lengthInBit": 2,
        "type": "bitfield",
        "transform": "P1"
    },
    {
        "key": "gkReflexes",
        "startByte": 44,
        "startBit": 6,
        "lengthInBit": 7,
        "type": "bitfield"
    },
    {
        "key": "kickingPower",
        "startByte": 44,
        "startBit": 13,
        "lengthInBit": 7,
        "type": "bitfield"
    },
    {
        "key": "weakFootAccuracy",
        "startByte": 36,
        "startBit": 30,
        "lengthInBit": 2,
        "type": "bitfield",
        "transform": "P1"
    },
    {
        "key": "scissorsFeint",
        "startByte": 48,
        "startBit": 6,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "doubleTouch",
        "startByte": 48,
        "startBit": 7,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "flipFlap",
        "startByte": 48,
        "startBit": 8,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "marseilleTurn",
        "startByte": 48,
        "startBit": 9,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "sombrero",
        "startByte": 48,
        "startBit": 10,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "crossOverTurn",
        "startByte": 48,
        "startBit": 11,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "cutBehindAndTurn",
        "startByte": 48,
        "startBit": 12,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "scotchMove",
        "startByte": 48,
        "startBit": 13,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "stepOnSkillControl",
        "startByte": 48,
        "startBit": 14,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "headingSkill",
        "startByte": 48,
        "startBit": 15,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "longRangeDrive",
        "startByte": 48,
        "startBit": 16,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "chipShotControl",
        "startByte": 48,
        "startBit": 17,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "longRangeShooting",
        "startByte": 48,
        "startBit": 18,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "knuckleShot",
        "startByte": 48,
        "startBit": 19,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "dippingShot",
        "startByte": 48,
        "startBit": 20,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "risingShot",
        "startByte": 48,
        "startBit": 21,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "acrobaticFinishing",
        "startByte": 48,
        "startBit": 22,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "heelTrick",
        "startByte": 48,
        "startBit": 23,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "firstTimeShot",
        "startByte": 48,
        "startBit": 24,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "oneTouchPass",
        "startByte": 48,
        "startBit": 25,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "throughPassing",
        "startByte": 48,
        "startBit": 26,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "weightedPass",
        "startByte": 48,
        "startBit": 27,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "pinpointCrossing",
        "startByte": 48,
        "startBit": 28,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "outsideCurler",
        "startByte": 48,
        "startBit": 29,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "rabona",
        "startByte": 48,
        "startBit": 30,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "noLookPass",
        "startByte": 48,
        "startBit": 31,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "lowLoftedPass",
        "startByte": 52,
        "startBit": 0,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "gkLowPunt",
        "startByte": 52,
        "startBit": 1,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "gkHighPunt",
        "startByte": 52,
        "startBit": 2,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "longThrow",
        "startByte": 52,
        "startBit": 3,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "gkLongThrow",
        "startByte": 52,
        "startBit": 4,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "penaltySpecialist",
        "startByte": 52,
        "startBit": 5,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "gkPenaltySaver",
        "startByte": 52,
        "startBit": 6,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "gamesmanship",
        "startByte": 52,
        "startBit": 7,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "manMarking",
        "startByte": 52,
        "startBit": 8,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "trackBack",
        "startByte": 52,
        "startBit": 9,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "interception",
        "startByte": 52,
        "startBit": 10,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "acrobaticClear",
        "startByte": 52,
        "startBit": 11,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "captaincy",
        "startByte": 52,
        "startBit": 12,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "superSub",
        "startByte": 52,
        "startBit": 13,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "fightingSpirit",
        "startByte": 52,
        "startBit": 14,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "playingStyle",
        "startByte": 32,
        "startBit": 18,
        "lengthInBit": 5,
        "type": "bitfield",
        "transform": "nB"
    },
    {
        "key": "trickster",
        "startByte": 44,
        "startBit": 31,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "mazingRun",
        "startByte": 48,
        "startBit": 0,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "speedingBullet",
        "startByte": 48,
        "startBit": 1,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "incisiveRun",
        "startByte": 48,
        "startBit": 2,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "longBallExpert",
        "startByte": 48,
        "startBit": 3,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "earlyCross",
        "startByte": 48,
        "startBit": 4,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "longRanger",
        "startByte": 48,
        "startBit": 5,
        "lengthInBit": 1,
        "type": "bitfield",
        "transform": "j"
    },
    {
        "key": "reputation",
        "startByte": 32,
        "startBit": 28,
        "lengthInBit": 3,
        "type": "bitfield",
        "transform": "P1"
    },
    {
        "key": "dribHunch",
        "startByte": 36,
        "startBit": 21,
        "lengthInBit": 3,
        "type": "bitfield",
        "transform": "P1"
    },
    {
        "key": "dribArmMove",
        "startByte": 16,
        "startBit": 28,
        "lengthInBit": 4,
        "type": "bitfield",
        "transform": "P1"
    },
    {
        "key": "runHunch",
        "startByte": 36,
        "startBit": 24,
        "lengthInBit": 3,
        "type": "bitfield",
        "transform": "P1"
    },
    {
        "key": "runArmMove",
        "startByte": 20,
        "startBit": 28,
        "lengthInBit": 4,
        "type": "bitfield",
        "transform": "P1"
    },
    {
        "key": "dribMotion",
        "startByte": 40,
        "startBit": 11,
        "lengthInBit": 2,
        "type": "bitfield",
        "transform": "P1"
    },
    {
        "key": "ckMotion",
        "startByte": 24,
        "startBit": 28,
        "lengthInBit": 4,
        "type": "bitfield",
        "transform": "P1"
    },
    {
        "key": "fkMotion",
        "startByte": 32,
        "startBit": 23,
        "lengthInBit": 5,
        "type": "bitfield",
        "transform": "P1"
    },
    {
        "key": "pkMotion",
        "startByte": 36,
        "startBit": 27,
        "lengthInBit": 3,
        "type": "bitfield",
        "transform": "P1"
    },
    {
        "key": "playerAppearance",
        "startByte": 240,
        "length": 72,
        "type": "raw_bytes"
    }
]


def read_string(data: bytes | bytearray, offset: int, length: int) -> str:
    chunk = bytes(data[offset:offset + length])
    chunk = chunk.split(b"\x00", 1)[0]
    # UTF-8 is the behavior of the original script; fallback helps with diagnostics.
    return chunk.decode("utf-8", errors="replace").strip()


def read_bitfield(data, byte_offset: int, bit_offset: int, bit_length: int, signed=False) -> int:
    value = 0
    first_byte = byte_offset + bit_offset // 8
    first_bit = bit_offset % 8
    for i in range(bit_length):
        byte_idx = first_byte + (first_bit + i) // 8
        bit_idx = (first_bit + i) % 8
        if byte_idx >= len(data):
            raise ValueError("Bit field exceeds the buffer.")
        value |= ((data[byte_idx] >> bit_idx) & 1) << i
    if signed and value & (1 << (bit_length - 1)):
        value -= 1 << bit_length
    return value


def write_bitfield(data, byte_offset: int, bit_offset: int, bit_length: int, value: int) -> None:
    value = int(value)
    if not 0 <= value < (1 << bit_length):
        raise ValueError(f"Value {value} out of range 0..{(1 << bit_length)-1}.")
    first_byte = byte_offset + bit_offset // 8
    first_bit = bit_offset % 8
    for i in range(bit_length):
        byte_idx = first_byte + (first_bit + i) // 8
        bit_idx = (first_bit + i) % 8
        if byte_idx >= len(data):
            raise ValueError("Bit field exceeds the buffer.")
        mask = 1 << bit_idx
        if (value >> i) & 1:
            data[byte_idx] |= mask
        else:
            data[byte_idx] &= ~mask


def transform_from_raw(raw_value, transform):
    if transform == "P1":
        return raw_value + 1
    if transform == "j":
        return bool(raw_value)
    if transform == "l4":
        return {0: "R", 1: "L"}.get(raw_value, raw_value)
    if transform == "dt":
        return {0: "C", 1: "B", 2: "A", 3: "B3"}.get(raw_value, "N/A")
    if transform == "eB":
        return POS_ORDER[raw_value] if 0 <= raw_value < len(POS_ORDER) else raw_value
    if transform == "nB":
        return {
            0: None, 1: "goalPoacher", 2: "dummyRunner", 3: "foxInTheBox",
            4: "targetMan", 5: "creativePlaymaker", 6: "prolificWinger",
            7: "roamingFlank", 8: "crossSpecialist", 9: "classicNo10",
            10: "holePlayer", 11: "boxToBox", 12: "theDestroyer",
            13: "orchestrator", 14: "anchorMan", 15: "offensiveFullBack",
            16: "fullBackFinisher", 17: "defensiveFullBack", 18: "buildUp",
            19: "extraFrontman", 20: "offensiveGoalkeeper", 21: "defensiveGoalkeeper"
        }.get(raw_value, raw_value)
    return raw_value


def transform_to_raw(value, transform):
    if transform == "P1":
        return int(value) - 1
    if transform == "j":
        if isinstance(value, str):
            return 1 if value.strip().lower() in ("1", "true", "yes", "sim", "on") else 0
        return 1 if value else 0
    if transform == "l4":
        mapping = {"R": 0, "L": 1, "r": 0, "l": 1}
        return mapping.get(value, int(value) if str(value).lstrip("-").isdigit() else value)
    if transform == "dt":
        mapping = {"C": 0, "B": 1, "A": 2, "B3": 3, "N/A": 0}
        return mapping.get(str(value).upper(), mapping.get(str(value), int(value) if str(value).isdigit() else value))
    if transform == "eB":
        return POS_ORDER.index(value) if value in POS_ORDER else int(value)
    if transform == "nB":
        mapping = {
            "None": 0, "goalPoacher": 1, "dummyRunner": 2, "foxInTheBox": 3,
            "targetMan": 4, "creativePlaymaker": 5, "prolificWinger": 6,
            "roamingFlank": 7, "crossSpecialist": 8, "classicNo10": 9,
            "holePlayer": 10, "boxToBox": 11, "theDestroyer": 12,
            "orchestrator": 13, "anchorMan": 14, "offensiveFullBack": 15,
            "fullBackFinisher": 16, "defensiveFullBack": 17, "buildUp": 18,
            "extraFrontman": 19, "offensiveGoalkeeper": 20, "defensiveGoalkeeper": 21
        }
        if value is None:
            return 0
        return mapping.get(str(value), int(value) if str(value).isdigit() else value)
    return value


def get_field(record: bytes | bytearray, field: dict):
    key = field["key"]
    offset = field.get("startByte", 0)
    kind = field["type"]
    if kind == "string":
        return read_string(record, offset, field["length"])
    if kind == "raw_bytes":
        return bytes(record[offset:offset + field.get("length", 0)]).hex()
    if kind == "bitfield":
        value = read_bitfield(record, offset, field.get("startBit", 0),
                              field["lengthInBit"], field.get("signed", False))
        return transform_from_raw(value, field.get("transform"))
    if kind == "bytes":
        length = field.get("length", 1)
        chunk = bytes(record[offset:offset + length])
        value = int.from_bytes(chunk, "little", signed=field.get("signed", False))
        return transform_from_raw(value, field.get("transform"))
    return None


def set_field(record: bytearray, field: dict, value) -> None:
    key = field["key"]
    offset = field.get("startByte", 0)
    kind = field["type"]
    transform = field.get("transform")
    raw_value = transform_to_raw(value, transform)
    if kind == "string":
        encoded = str(value).encode("utf-8")
        length = field["length"]
        if len(encoded) > length:
            raise ValueError(f"{key}: texto tem {len(encoded)} bytes; máximo {length}.")
        record[offset:offset + length] = encoded.ljust(length, b"\x00")
        return
    if kind == "raw_bytes":
        raw = bytes.fromhex(str(value).replace(" ", ""))
        length = field.get("length", len(raw))
        if len(raw) != length:
            raise ValueError(f"{key}: esperado {length} bytes em hexadecimal.")
        record[offset:offset + length] = raw
        return
    if kind == "bitfield":
        write_bitfield(record, offset, field.get("startBit", 0), field["lengthInBit"], int(raw_value))
        return
    if kind == "bytes":
        length = field.get("length", 1)
        raw_value = int(raw_value)
        min_value = -(1 << (length * 8 - 1)) if field.get("signed") else 0
        max_value = (1 << (length * 8 - (1 if field.get("signed") else 0))) - 1
        if not min_value <= raw_value <= max_value:
            raise ValueError(f"{key}: valor fora do intervalo {min_value}..{max_value}.")
        record[offset:offset + length] = raw_value.to_bytes(length, "little", signed=field.get("signed", False))
        return
    raise ValueError(f"Field {key} not supported for writing.")

FIELD_BY_NAME = {f["key"]: f for f in PLAYER_FIELDS}
