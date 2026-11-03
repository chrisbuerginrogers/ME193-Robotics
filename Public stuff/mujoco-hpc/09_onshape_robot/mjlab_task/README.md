# Train the robot to drive straight with mjlab

`drive_task.py` turns your Onshape robot (`../onshape/robot.xml`) into an [mjlab](https://github.com/mujocolab/mjlab)
reinforcement-learning task. 4096 copies of the robot start slightly off-angle and learn to drive down +x while staying
on the line y = 0. The policy outputs one speed per wheel.

mjlab trains only on an NVIDIA GPU, so training runs on the cluster. (On a Mac it can only play back.)

| File | What it is |
|---|---|
| `drive_task.py` | The task: robot, rewards, resets. **Tune this one.** |
| `train.py`, `play.py` | mjlab's own train/play commands, with our task registered first |
| `train.sbatch` | A Slurm job that trains on a GPU, for running by hand on the cluster |

Everything runs from your laptop with `runIt.py`, in the `mujoco-hpc` folder (venv active, VPN on if off campus).

## 1. Install (once)

`python3 setup.py` installs mjlab into `~/mujoco-env` on the cluster along with MuJoCo. It is about 6 GB of your 28 GB
home quota, so check `quota -s` first and free space with `python3 cleanup.py` if you are short. If you set up the
cluster before mjlab was added, rerun `python3 setup.py --reinstall`.

## 2. Check the task loads (short run)

```
python3 runIt.py --gpu --time 00:10:00 --mem 16G --cpus 4 \
  --with 09_onshape_robot/mjlab_task/drive_task.py --with 09_onshape_robot/onshape \
  09_onshape_robot/mjlab_task/train.py Drive-Straight --env.scene.num-envs 64
```
Under "job output" you should see training iterations with a mean reward. If it stops with an error instead, the
message says what to fix in `drive_task.py` (see Tuning).

## 3. Train

Same command with more robots and time (`runIt.py` waits until the job ends, so keep the terminal open):
```
python3 runIt.py --gpu --time 01:00:00 --mem 16G --cpus 4 \
  --with 09_onshape_robot/mjlab_task/drive_task.py --with 09_onshape_robot/onshape \
  09_onshape_robot/mjlab_task/train.py Drive-Straight --env.scene.num-envs 4096
```
The logs and checkpoints (`model_<n>.pt`, saved every 50 of 500 iterations) come back to
`runs/<name>/logs/rsl_rl/drive_straight/<date>/` on your laptop.

## 4. Watch the result

mjlab can play a trained policy on a Mac (it only cannot train there). Install it in your laptop venv, copy
`09_onshape_robot/mjlab_task/drive_task.py` next to `play.py`, and run:
```
python3 -m pip install mjlab
python play.py Drive-Straight --checkpoint-file runs/<name>/logs/rsl_rl/drive_straight/<date>/model_499.pt
```

## Tuning (all in `drive_task.py`)

- **Wheels barely turn or the robot crawls:** raise `WHEEL_KD` or `WHEEL_TORQUE_LIMIT`. The motor pushes with
  `WHEEL_KD * (asked speed - actual speed)` N*m, capped at the limit. Start by checking that `play.py --agent random`
  looks lively.
- **Robot jerks and flips:** lower `WHEEL_TORQUE_LIMIT`, or make the `action_rate` reward weight more negative.
- **It drives straight but slowly:** raise `TARGET_SPEED`. It is rewarded for matching that speed, not for going faster.
- **It wiggles along the line:** raise the `stay_on_line` and `face_forward` weights, lower `START_YAW`.
- **Make it harder:** raise `START_YAW`, or add friction and mass randomization (mjlab's `mjlab.envs.mdp.dr`) so the
  policy copes with the jerkiness of your rod wheels and not one exact friction value.

## Not tested

This task was written against mjlab's source but has **not been run yet**. Expect to fix a typo or two at step 2. Please report what you had to change.
