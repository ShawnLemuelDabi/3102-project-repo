FROM python:3.8

RUN git clone https://github.com/batra-mlp-lab/visdial-rl.git

COPY requirements.txt /visdial-rl/requirements.txt

COPY main1-1.py /visdial-rl/main1-1.py

WORKDIR /visdial-rl

RUN pip install -r requirements.txt

# Processed dialog data for VisDial v0.5
RUN wget -P data/visdial/ https://s3.amazonaws.com/cvmlp/visdial-pytorch/data/chat_processed_data.h5
RUN wget -P data/visdial/ https://s3.amazonaws.com/cvmlp/visdial-pytorch/data/chat_processed_data_gencaps.h5
RUN wget -P data/visdial/ https://s3.amazonaws.com/cvmlp/visdial-pytorch/data/chat_processed_params.json

# Processed image features for VisDial v0.5, using VGG-19
RUN wget -P data/visdial/ https://s3.amazonaws.com/cvmlp/visdial-pytorch/data/data_img.h5

# SL checkpoints
RUN wget -P checkpoints/ https://s3.amazonaws.com/cvmlp/visdial-pytorch/models/abot_sl_ep60.vd
RUN wget -P checkpoints/ https://s3.amazonaws.com/cvmlp/visdial-pytorch/models/qbot_sl_ep60.vd

# SL-Delta checkpoints
RUN wget -P checkpoints/ https://s3.amazonaws.com/cvmlp/visdial-pytorch/models/abot_sl_ep15_delta.vd
RUN wget -P checkpoints/ https://s3.amazonaws.com/cvmlp/visdial-pytorch/models/qbot_sl_ep15_delta.vd


# RL checkpoints
RUN wget -P checkpoints/ https://s3.amazonaws.com/cvmlp/visdial-pytorch/models/abot_rl_ep10.vd
RUN wget -P checkpoints/ https://s3.amazonaws.com/cvmlp/visdial-pytorch/models/abot_rl_ep20.vd

RUN wget -P checkpoints/ https://s3.amazonaws.com/cvmlp/visdial-pytorch/models/qbot_rl_ep10.vd
RUN wget -P checkpoints/ https://s3.amazonaws.com/cvmlp/visdial-pytorch/models/qbot_rl_ep20.vd

# RL-Delta checkpoints
RUN wget -P checkpoints/ https://s3.amazonaws.com/cvmlp/visdial-pytorch/models/abot_rl_ep10_delta.vd
RUN wget -P checkpoints/ https://s3.amazonaws.com/cvmlp/visdial-pytorch/models/abot_rl_ep20_delta.vd

RUN wget -P checkpoints/ https://s3.amazonaws.com/cvmlp/visdial-pytorch/models/qbot_rl_ep10_delta.vd
RUN wget -P checkpoints/ https://s3.amazonaws.com/cvmlp/visdial-pytorch/models/qbot_rl_ep20_delta.vd

CMD [ "python", "./main1-1.py" ]