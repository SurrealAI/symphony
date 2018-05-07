# Design principles

If you are not sure about a specific design choice you want to make (especially for changes to the base API), please contact Jim and Jiren first. Please also let them know if you don't like any existing design choices.


1. **Keep simple things simple**. Think from the perspective of new users who know nothing. If they just want to use symphony to launch an embarrassingly parallel job, they should be able to do it with the _least amount_ of boilerplate. Do NOT prioritize expert users' need over novice's. If you want to add an advanced feature that would result in more code for the simplest task, you really need to rethink your design. 

2. **Allow as much flexibility as possible within the constraint of rule one**. Feel free to add default values and make reasonable assumptions, but keep them customizable for people who know what they are doing. Make sure you **add lots of docs** for the assumptions you make! 

3. **Minimize surprise**. This applies to veteran users, new users, and even our own backend developers. Again, think from the perspective of people who are not familiar with the internal workings of symphony. They shouldn't be surprised by extraneous concepts or terminology that only make sense under the hood. 
    - Example: we initially named two methods `add_lone_process()` and `add_process_group()`. For people who do not use the advanced `ProcessGroup` feature, however, the term `lone_process` doesn't make sense at all. We end up renaming `add_lone_process` to `add_process` and document their differences for users who know about `ProcessGroup`. 


# Case studies

All symphony backends should implement the following examples to stress-test both the code and API design. Please also heavily comment your example scripts, because they will serve as tutorials to showcase symphony's flexibility.

## Python socket: hello world

Use raw python socket to implement scenarios in which multiple processes and multiple process groups communicating with each other.

### 3 plain processes

- Process 0: send `"hello0 {i}"` to P1, and receive `"hello2 {i}"` from P2
- Process 1: send `"hello1 {i}"` to P2, and receive `"hello0 {i}"` from P0
- Process 2: send `"hello2 {i}"` to P0, and receive `"hello1 {i}"` from P1

iterate over `i` forever

### Mix process and process group

Same messages as above, except that process 1 and 2 are now in a process group.

- Process 0 (standalone)
- ProcessGroup
    - Process 1
    - Process 2

## ZeroMQ: numerical integration

Use ZMQ to implement a hierarchical reduce algorithm for numerical integration. Concrete example: compute the integral of `f(x) = x ** 2` from 0 to 10.

Topology:

- Process 0 (standalone process with no group): supermaster "S0"
- ProcessGroup 0
    - Process 0: groupmaster "G0"
    - Process 1: worker "W01"
    - Process 2: worker "W02"
- ProcessGroup 1
    - Process 0: groupmaster "G1"
    - Process 1: worker "W11"
    - Process 2: worker "W12"
    - Process 3: worker "W13"
    - Process 4: worker "W14"
   
   
Communication: 

1. Supermaster divides the task into 10 chunks: `[0, 1)`, `[1, 2)`, ..., `[9, 10]`. We call them `supertasks[0]` to `supertasks[9]`. 

2. Supermaster divides `supertask[0]` into 2 chunks, `G0task: [0, 1/2)`, and `G1task: [1/2, 1]`. 

3. Supermaster broadcasts the array `[G0task, G1task]` to groupmasters G0 and G1. They both receive the same array, but G0 takes `G0task` at index 0 and G1 takes `G1task` at index 1.

4. G0 further divides `G0task` into 2 sub-ranges: `W01task [0, 1/4)` and `W02task [1/4, 1/2]`. It broadcasts the array `[W01, W02]` to its two workers. The workers compute the numerical integration of `f(x)` in those ranges. Likewise, G1 divides `G1task` into 4 sub-ranges and distribute to its 4 workers.
 
5. Workers in group 0 finish the computation and send results to G0, which add them up. Workers in group 1 also reduce their results on G1.

6. G0 and G1 send results to S0, which sums them up as the final result for `supertasks[0]`. 

7. S0 move on to distribute the next `supertasks[1]`, and repeat step 2 - 6 until all 10 supertasks are done. 

8. S0 adds up all 10 supertask results and report the integration value. It then sends a termination signal to all groupmasters and workers, before terminating itself. 


## PyTorch multi-GPU MNIST

TODO

Topology

- ProcessGroup
    - GPU 0
    - GPU 1
    - GPU 2
    - GPU 3
- Evaluation process, periodically load checkpoint
- Tensorboard process
