# Requirements

SRL is designed as an application that relies on Docker. Hence, users need [`Docker`](https://docs.docker.com/) to build and run SRL.

Get it from https://docs.docker.com/engine/installation/#supported-platforms

# Running

Run your Docker instance and then type the following command on terminal:

```
docker-compose up corenlpsrl
``` 


Then, in a new shell, go to the srl_example folder and type

```
cd srl_example
docker build -t python-barcode .
docker run  --network=srldocker_srlnet python-barcode
``` 

If you want to change the example sentence, just type a new one in the Dockerfile file (last row) and repeat the last two commands
