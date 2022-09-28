# Getting Started

## Front End

1. https://www.youtube.com/watch?v=LWhnS5elz4o&ab_channel=NaderDabit

## Visual Question Generator 1-1

1. cd vis_qn_gen_1_1/non-docker
2. create a new venv and activate it
    a. python -m virtualenv .
    b. Scripts\activate
3. run "pip install -r requirements.txt"
4. run "download_preprocessed_and_checkpoints.bat" (this only needs to run the first time)
5. cd visdial-rl and run "run_when_not_in_docker.py"

## Generate Captions 1-2

1. cd generate_captions_1_2/non-docker
2. run "generate_captions.py". This will download a large file.
3. After running once, check generate_captions.py and look at line 30 to 32, I put further instructions there to prevent re-downloading the file
4. run step 2 again.

# TODOs

1. Modularise both scripts.
2. Put in docker.
3. design the front end
