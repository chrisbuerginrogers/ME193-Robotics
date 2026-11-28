# Flag LLM: a tiny language model on the LEGO Education CS&AI kit

A 90-minute hands-on activity for senior mechanical engineering students that teaches how
LLMs / transformers work. Students train a language model whose "words" are flag colors;
a LEGO robot reads a prompt with a color sensor, predicts the next stripe on a pointer dial,
and "paints" invented flags.

This README is the project brief for development. It contains the design decisions,
the full flag dataset, the LEGO API rules, and open tasks.

---

## 1. Core idea

- A flag is a sentence: `<REGION> stripe stripe stripe <END>`
  - Example: Italy = `<EUROPE> green azure red <END>` (azure stands for white; see section 3)
- An LLM does one thing: given the tokens so far, output a probability for every possible
  next token. Then sample one, append it, repeat until `<END>`.
- Three models, compared in class:
  1. **Bigram**: P(next | previous token). Loses the region after the first stripe.
  2. **Region bigram**: P(next | region, previous token). 4x the parameters, barely better
     (most table cells see no data). Shows why bigger lookup tables do not scale.
  3. **One-head attention**: every context token casts a vote; attention weights the votes.
     Clearly best on unseen flags.

## 2. Hardware and roles

| Device | Python class | Role |
| --- | --- | --- |
| Double Motor robot | `le.DoubleMotor()` | "Paints" each generated stripe: light shows the color, drives forward one stripe |
| Single Motor + pointer arm | `le.SingleMotor()` | Points at the predicted next token on a printed 8-sector dial |
| Color Sensor | `le.ColorSensor()` | Reads prompt tiles one at a time |
| Controller | `le.Controller()` | Left lever = region (prompt), right lever = temperature |

Every script must also run with `--sim` (keyboard input instead of hardware).

## 3. Tokenization

The kit has exactly 8 colors: GREEN, BLUE, RED, ORANGE, YELLOW, AZURE, PURPLE, MAGENTA.
Real flag colors are mapped to 7 stripe tokens. The information loss is deliberate and is a
teaching point (real tokenizers also lose information).

| Real color | Token | Consequence |
| --- | --- | --- |
| white | `azure` | |
| black | `purple` | |
| light blue | `blue` | Luxembourg becomes identical to the Netherlands |
| gold | `yellow` | |
| saffron | `orange` | India becomes identical to Niger |
| maroon / carmine | `red` | |
| (none) | `magenta` | Unused; sensor reading of magenta = invalid tile |

Special tokens (never read from a tile):
- Region tokens: `<EUROPE>`, `<AFRICA>`, `<ASIA>`, `<AMERICAS>` (set by the Controller's left lever)
- `<END>`: only ever produced by the model; robot beeps and stops

Model outputs = 7 colors + `<END>` = 8 tokens = 8 dial sectors, in this order (45 deg each,
pointer starts on red):

`red, orange, yellow, green, blue, azure, purple, <END>`

Reading order: horizontal stripes top to bottom; vertical stripes left to right (hoist to fly).
Orientation is recorded in the data but not used by the current model (possible extension).

## 4. Flag dataset

71 flags with simple stripes. Regions follow the UN geoscheme (so Armenia and Azerbaijan are
Asia). Stars, emblems, coats of arms, fimbriations and stripe widths are ignored;
`simplified=yes` means a visible feature was dropped. Syria and Afghanistan are excluded
(flags recently changed or contested).

**VERIFY every row against an authoritative source before class.** This list was compiled
from memory, including the orientation column.

`real_stripes` uses real color names separated by `;`. Apply the mapping in section 3 to get tokens.

```csv
region,country,orientation,real_stripes,simplified,notes
EUROPE,France,vertical,blue;white;red,no,
EUROPE,Italy,vertical,green;white;red,no,
EUROPE,Ireland,vertical,green;white;orange,no,
EUROPE,Belgium,vertical,black;yellow;red,no,
EUROPE,Romania,vertical,blue;yellow;red,no,same tokens as Chad
EUROPE,Germany,horizontal,black;red;gold,no,
EUROPE,Netherlands,horizontal,red;white;blue,no,
EUROPE,Luxembourg,horizontal,red;white;light blue,no,same tokens as Netherlands
EUROPE,Russia,horizontal,white;blue;red,no,
EUROPE,Slovakia,horizontal,white;blue;red,yes,coat of arms dropped
EUROPE,Serbia,horizontal,red;blue;white,yes,coat of arms dropped
EUROPE,Bulgaria,horizontal,white;green;red,no,
EUROPE,Hungary,horizontal,red;white;green,no,
EUROPE,Lithuania,horizontal,yellow;green;red,no,
EUROPE,Estonia,horizontal,blue;black;white,no,
EUROPE,Austria,horizontal,red;white;red,no,
EUROPE,Latvia,horizontal,carmine;white;carmine,yes,white band is narrow
EUROPE,Spain,horizontal,red;yellow;red,yes,coat of arms dropped; yellow is double width
EUROPE,Ukraine,horizontal,blue;yellow,no,
EUROPE,Poland,horizontal,white;red,no,
EUROPE,Monaco,horizontal,red;white,no,same as Indonesia
AFRICA,Nigeria,vertical,green;white;green,no,
AFRICA,Cote d'Ivoire,vertical,orange;white;green,no,reverse of Ireland
AFRICA,Niger,horizontal,orange;white;green,yes,orange disc dropped
AFRICA,Mali,vertical,green;gold;red,no,reverse of Guinea
AFRICA,Senegal,vertical,green;yellow;red,yes,star dropped
AFRICA,Guinea,vertical,red;yellow;green,no,
AFRICA,Ghana,horizontal,red;gold;green,yes,star dropped
AFRICA,Ethiopia,horizontal,green;yellow;red,yes,emblem dropped
AFRICA,Cameroon,vertical,green;red;yellow,yes,star dropped
AFRICA,Chad,vertical,blue;gold;red,no,
AFRICA,Gabon,horizontal,green;yellow;blue,no,
AFRICA,Sierra Leone,horizontal,green;white;blue,no,
AFRICA,Rwanda,horizontal,light blue;yellow;green,yes,sun dropped; blue band is wider
AFRICA,Egypt,horizontal,red;white;black,yes,eagle dropped
AFRICA,Libya,horizontal,red;black;green,yes,crescent and star dropped; black is double width
AFRICA,Malawi,horizontal,black;red;green,yes,sun dropped
AFRICA,Mauritius,horizontal,red;blue;yellow;green,no,only 4-stripe flag
AFRICA,The Gambia,horizontal,red;white;blue;white;green,no,white bands are thin
AFRICA,Botswana,horizontal,light blue;white;black;white;light blue,no,
ASIA,Indonesia,horizontal,red;white,no,
ASIA,Yemen,horizontal,red;white;black,no,
ASIA,Iraq,horizontal,red;white;black,yes,text dropped
ASIA,India,horizontal,saffron;white;green,yes,chakra dropped
ASIA,Iran,horizontal,green;white;red,yes,emblem and text dropped
ASIA,Tajikistan,horizontal,red;white;green,yes,crown and stars dropped
ASIA,Armenia,horizontal,red;blue;orange,no,
ASIA,Azerbaijan,horizontal,blue;red;green,yes,crescent and star dropped
ASIA,Uzbekistan,horizontal,light blue;white;green,yes,crescent; stars and red lines dropped
ASIA,Mongolia,vertical,red;blue;red,yes,soyombo dropped
ASIA,Laos,horizontal,red;blue;red,yes,white disc dropped; blue is double width
ASIA,Lebanon,horizontal,red;white;red,yes,cedar dropped
ASIA,Myanmar,horizontal,yellow;green;red,yes,star dropped
ASIA,Thailand,horizontal,red;white;blue;white;red,no,blue is double width
AMERICAS,Colombia,horizontal,yellow;blue;red,no,yellow is double width
AMERICAS,Ecuador,horizontal,yellow;blue;red,yes,coat of arms dropped
AMERICAS,Venezuela,horizontal,yellow;blue;red,yes,stars dropped
AMERICAS,Bolivia,horizontal,red;yellow;green,no,civil flag
AMERICAS,Peru,vertical,red;white;red,no,civil flag
AMERICAS,Canada,vertical,red;white;red,yes,maple leaf dropped
AMERICAS,Argentina,horizontal,light blue;white;light blue,yes,sun dropped
AMERICAS,Guatemala,vertical,light blue;white;light blue,yes,emblem dropped
AMERICAS,Honduras,horizontal,blue;white;blue,yes,stars dropped
AMERICAS,El Salvador,horizontal,blue;white;blue,yes,coat of arms dropped
AMERICAS,Nicaragua,horizontal,blue;white;blue,yes,coat of arms dropped
AMERICAS,Mexico,vertical,green;white;red,yes,emblem dropped
AMERICAS,Paraguay,horizontal,red;white;blue,yes,emblem dropped
AMERICAS,Haiti,horizontal,blue;red,yes,coat of arms dropped
AMERICAS,Barbados,vertical,ultramarine;gold;ultramarine,yes,trident dropped
AMERICAS,Costa Rica,horizontal,blue;white;red;white;blue,no,red is double width
AMERICAS,Suriname,horizontal,green;white;red;white;green,yes,star dropped
```

Add `ultramarine -> blue` to the mapping (Barbados).

Dataset stats: Europe 21, Africa 19, Americas 17, Asia 14. Lengths: 60 flags with 3 stripes,
5 with 2, 1 with 4, 5 with 5. Oceania is deliberately absent (too few striped flags), which is
a debrief point about training-data coverage.

Built-in puzzles worth keeping if the data is edited:
- Identical tokens, different regions: Romania / Chad; Bolivia / Guinea; Austria / Lebanon / Peru / Canada; Monaco / Indonesia; Italy / Iran / Mexico
- Reverses (order matters): Mali / Guinea; Ireland / Cote d'Ivoire
- Regional families: blue-white-blue (Central America); green-yellow-red (Africa); yellow-blue-red (Colombia, Ecuador, Venezuela)

## 5. Model specification

Pure Python, no ML libraries (students should be able to read it).

- `OUTPUTS` = 7 colors + `<END>`; `INPUTS` = 4 regions + 7 colors (11)
- Smoothing: add-alpha, alpha = 0.1
- **Bigram**: counts of next | previous. 11 x 8 = 88 parameters.
- **Region bigram**: counts of next | (region, previous). 4 x 11 x 8 = 352 parameters.
- **Attention (one head)**, for context tokens i = 0..t (token 0 is the region):
  - d_i = distance back from the slot being predicted (1 = newest token), capped at 6
  - value v_i = P(next | token_i sat d_i places back), learned by counting (skip-gram counts)
  - score_i = W[query = newest token, key = token_i] + D[d_i]
  - w = softmax(scores); P(next) = sum_i w_i * v_i
  - W (11 x 11) and D (6) learned by full-batch gradient ascent on mean log P(correct):
    d log P(y) / d score_i = w_i * (v_i(y) / P(y) - 1); lr = 3.0, 150 epochs, L2 = 0.001
  - During training, each flag's own counts are subtracted from the values it sees (no leakage)
  - 528 value + 121 W + 6 D = 655 parameters; trains in under 1 second
- **Temperature**: p^(1/T), renormalize; T <= 0.05 means argmax
- **Generation**: start from `[region] + prompt`, sample until `<END>` or 6 stripes

Reference results with this exact dataset (leave-one-out, train on 70, test on 1, x71):

| Model | Params | Top-1 correct | Avg P(correct) |
| --- | --- | --- | --- |
| Bigram | 88 | 33% | 27% |
| Region bigram | 352 | 34% | 28% |
| Attention | 655 | 53% | 38% |

Worksheet example that must keep working: prompt `<AFRICA> orange azure` gives scores
about (0.06, 0.33, 0.00), weights (0.31, 0.40, 0.29), P(green) about 0.52; bigram says blue.
`<EUROPE> green azure red` gives P(END) about 0.94 (bigram 0.46).

Known limitation (keep, it is a teaching point): one head can only add independent votes, so
it cannot combine "Africa AND green-white" (it slightly prefers red over green there).

## 6. LEGO API rules (critical)

The ONLY correct library is `legoeducation`:

```python
import legoeducation as le      # pip install legoeducation ; requires Python 3.14+
```

Never use `ev3dev`, `ev3dev2`, `pybricks`, `hub`/`spike` modules, `bricknil` or third-party BLE
libraries. If code contains `Motor('outB')`, `run_forever()`, `StopAction`, or port letters, it is
wrong (EV3 API).

Every hardware program follows this six-step pattern:

```python
import legoeducation as le

motor = le.SingleMotor()                                                 # 1. define
motor.connect(card_color=le.LEGO_COLOR_AZURE, card_serial="3683")        # 2. connect (team's own card)
if not motor.connected:                                                  # 3. check
    print("Error connecting to Single Motor.")
    exit(1)
motor.motor_run_for_degrees(360, speed=50)                               # 4. interact
print(f"Position: {motor.motor.position}")                               # 5. read
motor.disconnect()                                                       # 6. disconnect
```

Known functions and data (do not invent others; check `help(le.SingleMotor)` etc.):

- SingleMotor: `motor_run(direction=le.MOTOR_MOVE_DIRECTION_COUNTERCLOCKWISE, speed=50)`,
  `motor_run_for_degrees(degrees, speed=...)`, `motor_run_for_time(ms)`, `motor_set_speed(n)`,
  `motor_stop()`; data in `.motor`: `position`, `absolutePosition`, `speed`, `power`, `motorState`, `gesture`
- DoubleMotor: `movement_move_for_degrees(deg)`,
  `movement_move_for_time(time_ms=..., direction=le.MOVEMENT_DIRECTION_BACKWARD, speed=...)`,
  `movement_turn_for_degrees(degrees=..., direction=le.MOVEMENT_TURN_DIRECTION_LEFT)`,
  `motor_run_for_degrees(deg, motor=le.MOTOR_LEFT, speed=...)`; per-motor data
  `.motor[le.MOTOR_LEFT].position`; IMU data in `.imu_device`
- ColorSensor (read-only), `.sensor`: `color`, `reflection`, `rawRed`, `rawGreen`, `rawBlue`, `hue`, `saturation`, `value`
- Controller (read-only), `.sensor`: `leftPercent`, `rightPercent`, `leftAngle`, `rightAngle`
- All devices: `light_color(le.LEGO_COLOR_BLUE, pattern=le.LIGHT_PATTERN_BREATHE, intensity=100)`,
  `beep(pattern=le.SOUND_PATTERN_BEEP_SINGLE, frequency=440)`
- Colors: `le.LEGO_COLOR_` + GREEN, BLUE, RED, ORANGE, YELLOW, AZURE, PURPLE, MAGENTA

Environment: Bluetooth LE (Chromebooks cannot connect); devices must be charged, on, and not
connected in the LEGO Coding Canvas.

Unverified on real hardware (design around these):
- Whether `motor_run_for_degrees` blocks until the move finishes (current code sleeps after moves)
- Whether negative degrees reverse direction (current code only turns the pointer forward and tracks its sector)
- The Controller's lever value range (current code calibrates it; config `LEVER_MIN` / `LEVER_MAX`)
- Whether `.sensor.color` updates live without an explicit refresh call

## 7. Existing code layout

```
flag_llm/
  flags_data.py            dataset (tokens already mapped) + find_matches()
  model.py                 Bigram, RegionBigram, Attention, sample, generate, evaluate, leave_one_out
  hardware.py              Hardware class: six-step connect, read_tile, read_prompt, read_levers,
                           point_to, paint, end_signal, close; --sim fallback
  config.py                per-team Connection Cards and calibration constants
  show.py                  terminal bar charts and attention table
  0_check_hardware.py      instructor hardware check and lever calibration
  1_bigram_robot.py        Station 1: bigram table, robot paints generated flags
  2_attention_pointer.py   Station 2: attention weights/votes, pointer points to top token
  3_generate_temperature.py Station 3: region + temperature levers, logs generated_log.csv
  4_scaling_experiment.py  Debrief: params vs data on unseen flags (no hardware)
  make_dial.py             writes dial.svg / dial_mirrored.svg
```

Tile input: the student presses Enter for each tile, the script takes 5 sensor readings and
uses the majority; typing `g` ends the prompt.

## 8. Constraints for new code

- Audience: ME seniors with some Python; code must be short, readable and commented
- No ML libraries in the models (numpy is acceptable only for optional extensions)
- Keep every station runnable with `--sim`
- Keep the six-step pattern and the `connected` check; always disconnect in `finally`
- Keep the worksheet numbers in section 5 reproducible, or flag that the worksheet must be updated
- A full station must fit about 15-25 minutes of class time

## 9. Ideas / open tasks

- Read `real_stripes` from the CSV above and apply the mapping in code (instead of hard-coded tokens)
- Add a test suite (pytest) with a mock `legoeducation` module so hardware paths run in CI
- Orientation token (`<H>` / `<V>`) as an extension; does accuracy improve?
- Second attention head or a second layer to fix the "Africa AND green-white" limitation
- Live plot of the training loss and attention weights (matplotlib) for the projector
- Class-wide leaderboard from the generated logs (real vs invented rate per temperature)
- Detect white/black tiles via `reflection` so azure/purple can be freed up (needs testing)
- Third region source (e.g. Oceania) using the Controller lever instead of tiles
