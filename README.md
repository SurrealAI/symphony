Usecase: Using tmux for a dqn project and deploy ddpg project onto kubernetes
```
>>>> cd ~/dqn_project
>>>> python run.py # in run.py there is import symphony; cluster = symphony.use('dqn_tmux')
>>>> symph cluster dqn_tmux
>>>> symph list-experiments
>>>> symph cluster ddpg
>>>> 
```