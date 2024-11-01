@REM With GPU
docker run -d --gpus=all -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama:0.4.0-rc3

@REM CPU Only
docker run -d -v ollama:/root/.ollama -p 11434:11434 --name ollama ollama/ollama:0.4.0-rc3

docker exec -it ollama ollama run x/llama3.2-vision:11b 

