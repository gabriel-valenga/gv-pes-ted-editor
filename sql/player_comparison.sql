
SELECT
    -- Player identification
    pr.id AS player_record_id,
    pr.playerId AS pes_player_id,
    pr.playerName AS player_name,

    -- Player information
    pr.age,
    pr.height,
    pr.weight,
    pr.countryId1 AS nationality_id,
    pr.strongerFoot AS stronger_foot,
    pr.registeredPosition AS registered_position,
    pr.playingStyle AS playing_style,

    -- Team information
    t.id AS team_id,
    t.name AS team_name,
    t.team_type,

    -- TED and Option File information
    tf.id AS ted_file_id,
    tf.file_name AS ted_file_name,
    ofi.id AS option_file_id,
    opt.name AS option_file_name,

    -- Registered Overall
    pro.overall AS registered_overall,

    -- Positional Overalls
    MAX(CASE WHEN ppo.position = 'GK'  THEN ppo.overall END) AS overall_gk,
    MAX(CASE WHEN ppo.position = 'CB'  THEN ppo.overall END) AS overall_cb,
    MAX(CASE WHEN ppo.position = 'LB'  THEN ppo.overall END) AS overall_lb,
    MAX(CASE WHEN ppo.position = 'RB'  THEN ppo.overall END) AS overall_rb,
    MAX(CASE WHEN ppo.position = 'DMF' THEN ppo.overall END) AS overall_dmf,
    MAX(CASE WHEN ppo.position = 'CMF' THEN ppo.overall END) AS overall_cmf,
    MAX(CASE WHEN ppo.position = 'LMF' THEN ppo.overall END) AS overall_lmf,
    MAX(CASE WHEN ppo.position = 'RMF' THEN ppo.overall END) AS overall_rmf,
    MAX(CASE WHEN ppo.position = 'AMF' THEN ppo.overall END) AS overall_amf,
    MAX(CASE WHEN ppo.position = 'LWF' THEN ppo.overall END) AS overall_lwf,
    MAX(CASE WHEN ppo.position = 'RWF' THEN ppo.overall END) AS overall_rwf,
    MAX(CASE WHEN ppo.position = 'SS'  THEN ppo.overall END) AS overall_ss,
    MAX(CASE WHEN ppo.position = 'CF'  THEN ppo.overall END) AS overall_cf,

    -- Player attributes
    pr.attackingProwess,
    pr.ballControl,
    pr.dribbling,
    pr.tightPossession,
    pr.lowPass,
    pr.loftedPass,
    pr.finishing,
    pr.headingAbility,
    pr.placeKicking,
    pr.curl,
    pr.speed,
    pr.acceleration,
    pr.kickingPower,
    pr.jump,
    pr.physicalContact,
    pr.balance,
    pr.stamina,
    pr.defensiveProwess,
    pr.ballWinning,
    pr.aggression,

    -- Goalkeeper attributes
    pr.gkAwareness,
    pr.gkCatching,
    pr.gkClearing,
    pr.gkReach,
    pr.gkReflexes,

    -- Other player attributes
    pr.weakFootUsage,
    pr.weakFootAccuracy,
    pr.form,
    pr.injuryResistance,
    pr.attitude,
    pr.reputation,
    
    -- Player abilities
    CASE WHEN pr.scissorsFeint = 1 THEN 'TRUE' ELSE 'FALSE' END AS scissors_feint,
    CASE WHEN pr.doubleTouch = 1 THEN 'TRUE' ELSE 'FALSE' END AS double_touch,
    CASE WHEN pr.flipFlap = 1 THEN 'TRUE' ELSE 'FALSE' END AS flip_flap,
    CASE WHEN pr.marseilleTurn = 1 THEN 'TRUE' ELSE 'FALSE' END AS marseille_turn,
    CASE WHEN pr.sombrero = 1 THEN 'TRUE' ELSE 'FALSE' END AS sombrero,
    CASE WHEN pr.crossOverTurn = 1 THEN 'TRUE' ELSE 'FALSE' END AS cross_over_turn,
    CASE WHEN pr.cutBehindAndTurn = 1 THEN 'TRUE' ELSE 'FALSE' END AS cut_behind_and_turn,
    CASE WHEN pr.scotchMove = 1 THEN 'TRUE' ELSE 'FALSE' END AS scotch_move,
    CASE WHEN pr.stepOnSkillControl = 1 THEN 'TRUE' ELSE 'FALSE' END AS step_on_skill_control,
    CASE WHEN pr.headingSkill = 1 THEN 'TRUE' ELSE 'FALSE' END AS heading_skill,
    CASE WHEN pr.longRangeDrive = 1 THEN 'TRUE' ELSE 'FALSE' END AS long_range_drive,
    CASE WHEN pr.chipShotControl = 1 THEN 'TRUE' ELSE 'FALSE' END AS chip_shot_control,
    CASE WHEN pr.longRangeShooting = 1 THEN 'TRUE' ELSE 'FALSE' END AS long_range_shooting,
    CASE WHEN pr.knuckleShot = 1 THEN 'TRUE' ELSE 'FALSE' END AS knuckle_shot,
    CASE WHEN pr.dippingShot = 1 THEN 'TRUE' ELSE 'FALSE' END AS dipping_shot,
    CASE WHEN pr.risingShot = 1 THEN 'TRUE' ELSE 'FALSE' END AS rising_shot,
    CASE WHEN pr.acrobaticFinishing = 1 THEN 'TRUE' ELSE 'FALSE' END AS acrobatic_finishing,
    CASE WHEN pr.heelTrick = 1 THEN 'TRUE' ELSE 'FALSE' END AS heel_trick,
    CASE WHEN pr.firstTimeShot = 1 THEN 'TRUE' ELSE 'FALSE' END AS first_time_shot,
    CASE WHEN pr.oneTouchPass = 1 THEN 'TRUE' ELSE 'FALSE' END AS one_touch_pass,
    CASE WHEN pr.throughPassing = 1 THEN 'TRUE' ELSE 'FALSE' END AS through_passing,
    CASE WHEN pr.weightedPass = 1 THEN 'TRUE' ELSE 'FALSE' END AS weighted_pass,
    CASE WHEN pr.pinpointCrossing = 1 THEN 'TRUE' ELSE 'FALSE' END AS pinpoint_crossing,
    CASE WHEN pr.outsideCurler = 1 THEN 'TRUE' ELSE 'FALSE' END AS outside_curler,
    CASE WHEN pr.rabona = 1 THEN 'TRUE' ELSE 'FALSE' END AS rabona,
    CASE WHEN pr.noLookPass = 1 THEN 'TRUE' ELSE 'FALSE' END AS no_look_pass,
    CASE WHEN pr.lowLoftedPass = 1 THEN 'TRUE' ELSE 'FALSE' END AS low_lofted_pass,
    CASE WHEN pr.gkLowPunt = 1 THEN 'TRUE' ELSE 'FALSE' END AS gk_low_punt,
    CASE WHEN pr.gkHighPunt = 1 THEN 'TRUE' ELSE 'FALSE' END AS gk_high_punt,
    CASE WHEN pr.longThrow = 1 THEN 'TRUE' ELSE 'FALSE' END AS long_throw,
    CASE WHEN pr.gkLongThrow = 1 THEN 'TRUE' ELSE 'FALSE' END AS gk_long_throw,
    CASE WHEN pr.penaltySpecialist = 1 THEN 'TRUE' ELSE 'FALSE' END AS penalty_specialist,
    CASE WHEN pr.gkPenaltySaver = 1 THEN 'TRUE' ELSE 'FALSE' END AS gk_penalty_saver,
    CASE WHEN pr.gamesmanship = 1 THEN 'TRUE' ELSE 'FALSE' END AS gamesmanship,
    CASE WHEN pr.manMarking = 1 THEN 'TRUE' ELSE 'FALSE' END AS man_marking,
    CASE WHEN pr.trackBack = 1 THEN 'TRUE' ELSE 'FALSE' END AS track_back,
    CASE WHEN pr.interception = 1 THEN 'TRUE' ELSE 'FALSE' END AS interception,
    CASE WHEN pr.acrobaticClear = 1 THEN 'TRUE' ELSE 'FALSE' END AS acrobatic_clear,
    CASE WHEN pr.captaincy = 1 THEN 'TRUE' ELSE 'FALSE' END AS captaincy,
    CASE WHEN pr.superSub = 1 THEN 'TRUE' ELSE 'FALSE' END AS super_sub,
    CASE WHEN pr.fightingSpirit = 1 THEN 'TRUE' ELSE 'FALSE' END AS fighting_spirit,
    CASE WHEN pr.trickster = 1 THEN 'TRUE' ELSE 'FALSE' END AS trickster,
    CASE WHEN pr.mazingRun = 1 THEN 'TRUE' ELSE 'FALSE' END AS mazing_run,
    CASE WHEN pr.speedingBullet = 1 THEN 'TRUE' ELSE 'FALSE' END AS speeding_bullet,
    CASE WHEN pr.incisiveRun = 1 THEN 'TRUE' ELSE 'FALSE' END AS incisive_run,
    CASE WHEN pr.longBallExpert = 1 THEN 'TRUE' ELSE 'FALSE' END AS long_ball_expert,
    CASE WHEN pr.earlyCross = 1 THEN 'TRUE' ELSE 'FALSE' END AS early_cross,
    CASE WHEN pr.longRanger = 1 THEN 'TRUE' ELSE 'FALSE' END AS long_ranger,
    
    -- Player position proficiency
    pr.positionGk,
    pr.positionCb,
    pr.positionLb,
    pr.positionRb,
    pr.positionDmf,
    pr.positionCmf,
    pr.positionLmf,
    pr.positionRmf,
    pr.positionAmf,
    pr.positionLwf,
    pr.positionRwf,
    pr.positionSs,
    pr.positionCf

FROM player_records pr

INNER JOIN ted_files tf
    ON tf.id = pr.ted_file_id

INNER JOIN option_file_imports ofi
    ON ofi.id = tf.import_id

INNER JOIN option_files opt
    ON opt.id = ofi.option_file_id

LEFT JOIN teams t
    ON t.id = tf.team_id

LEFT JOIN player_registered_overalls pro
    ON pro.player_record_id = pr.id
    AND pro.calculation_version = '1'

LEFT JOIN player_position_overalls ppo
    ON ppo.player_record_id = pr.id
    AND ppo.calculation_version = '1'

GROUP BY
    pr.id

ORDER BY
    pr.playerName COLLATE NOCASE;
