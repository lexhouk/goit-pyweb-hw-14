docker build -t sphinxdoc_builder .
docker run -v $PWD:/sphinx -w /sphinx -it sphinxdoc_builder make -C docs html
