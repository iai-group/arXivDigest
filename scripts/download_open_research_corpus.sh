#!/usr/bin/env sh

curr_dir=$(dirname "$(readlink -f "$0")")
data_dir=$curr_dir/data/open_research_corpus

if [ ! -d $data_dir ]; then
    mkdir $data_dir
fi

cd $data_dir
wget https://s3-us-west-2.amazonaws.com/ai2-s2-research-public/open-corpus/2021-02-01/manifest.txt
wget -B https://s3-us-west-2.amazonaws.com/ai2-s2-research-public/open-corpus/2021-02-01/ -i manifest.txt
