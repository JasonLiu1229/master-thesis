# Master thesis: Renaming identifiers using LLM

## Tools

In the `tools/` folder you can find several tools I made to help you with running this project.
In case you are running this on Windows, you can use the `change_java_version.ps1` to switch java versions in case needed.
In linux this is done by changing the `JAVA_HOME` variable.

There is also additionaly a database processing library, specifically made for `method2test`.

## Enviroment variables

Note this project makes use of private enviroment variables. This is because we work with api keys and to inialize this, you need to generate one for your own model. This is only applied for the API version of this project.

These are the keys that needs to be specified in your `.env` file:

```txt
    API_KEY=sk-example-api-code
    API_URL=https://api.example.com

    SERVER_SECRET=super_secret_key
```

NOTE: **DO NOT** add your enviroment variables to the repository or anywhere public.

## Technique information

### T1 (GNN)

### T2 (RefBert)

### T3

#### Open source model, not fine tuned

#### Open source model, fine tuned

#### Paid model, not fine tuned

## Setup steps

### Prerequirements

- Docker
- Python (Optionally with Poetry)
  - Version 3.12.4 for main software
  - Version 3.8.4 for Refbert (benchmarking)
  - Version 3.7 for GNN (benchmarking)
- Rust (for one the tooling)
- Java (depending on what you want, you might need to install different versions of Java)
- For benchmarking, additionally you need Arno's setup. See references for more info.
  - Note that database generation is not performed inside Docker; you must generate the database manually if you want to reproduce the benchmarking.
  - Additionally, some files must be edited manually to resolve incompatibilities.

Note: Windows might need seperate compilers to make some things work. This is needed for `pybind11` and other libraries. Additionally if using docker, some things do not have to be directly installed, like Python.

### Steps

#### Benchmarking

Benchmarking is done using docker containers. To fully seperate each technique from interfering with each other, we setup a docker container for each technique and parse the results to a seperate file. So make sure docker is installed and working.

To run the benchmarking, you need to make sure that the [replication package](https://www.dropbox.com/scl/fo/fd9hhq7ejo743297hgv26/AA82GK-zdu4689E0ZeZwGHo?rlkey=vreei6ybneqkfqjpsywli0dt0&e=1&st=ol319nja&dl=0) is downloaded. Check references for the original author for this code.

Also make sure the `compose.yml` file is set correctly. The pathing for the replication can mismatch based on your download loacation and naming of the file.

The benchmarking itself is a simple docker run command: `docker compose --profile benchmark`. Be aware that this will generate nothing usefull if the other techniques are not ran themselves. The other techniques can be found in the `compose.yml` to find what profile they are set to. After running the needed techniques for your study, you can run benchmark and see a `benchmark.csv` file generated where all results are combined.

#### LLM tuning

The tuning code consist of two parts, one is the data preprocessing and the other is the tuning itself.

##### Data preprocessing

Again this is also dockerized so you do not have to run any special commands besides docker to make this work. The data preprocesing does need the dataset that you want to preprocess in a specific format:

```jsonl
{
  prompt: {
    # obf code
  },
  response: {
    # gt code
  }
}
```

So be aware of this.

After running the preprocess code, three folders will be generated. These will consist of the dataset in a `.arrow` format.

##### Tuning

The tuning is done using [QLoRA](https://medium.com/@dillipprasad60/qlora-explained-a-deep-dive-into-parametric-efficient-fine-tuning-in-large-language-models-llms-c1a4794b1766), just know that it is a fine tuning task to tune a model for a specific task or domain. So perfect for us.

Overall you can just run `docker compose --profile tune up` to run the preprocess and tuning simaltainiously. Note in this repo the dataset is already preprocessed for you, so if you want to use a different one, add `--force` in the Dockerfile that can be found in `docker/tuner.Dockerfile`.

## References

```bibtex
@thesis{dekeersmaeker2023enhancing,
  author       = {De Keersmaeker, Arno},
  title        = {Enhancing Test Code Understandability with Machine Learning-Based Identifier Naming},
  school       = {University of Antwerp},
  year         = {2023},
  type         = {Master's Thesis}
}
@article{hui2024qwen2,
      title={Qwen2. 5-Coder Technical Report},
      author={Hui, Binyuan and Yang, Jian and Cui, Zeyu and Yang, Jiaxi and Liu, Dayiheng and Zhang, Lei and Liu, Tianyu and Zhang, Jiajun and Yu, Bowen and Dang, Kai and others},
      journal={arXiv preprint arXiv:2409.12186},
      year={2024}
}
@article{qwen2,
      title={Qwen2 Technical Report}, 
      author={An Yang and Baosong Yang and Binyuan Hui and Bo Zheng and Bowen Yu and Chang Zhou and Chengpeng Li and Chengyuan Li and Dayiheng Liu and Fei Huang and Guanting Dong and Haoran Wei and Huan Lin and Jialong Tang and Jialin Wang and Jian Yang and Jianhong Tu and Jianwei Zhang and Jianxin Ma and Jin Xu and Jingren Zhou and Jinze Bai and Jinzheng He and Junyang Lin and Kai Dang and Keming Lu and Keqin Chen and Kexin Yang and Mei Li and Mingfeng Xue and Na Ni and Pei Zhang and Peng Wang and Ru Peng and Rui Men and Ruize Gao and Runji Lin and Shijie Wang and Shuai Bai and Sinan Tan and Tianhang Zhu and Tianhao Li and Tianyu Liu and Wenbin Ge and Xiaodong Deng and Xiaohuan Zhou and Xingzhang Ren and Xinyu Zhang and Xipin Wei and Xuancheng Ren and Yang Fan and Yang Yao and Yichang Zhang and Yu Wan and Yunfei Chu and Yuqiong Liu and Zeyu Cui and Zhenru Zhang and Zhihao Fan},
      journal={arXiv preprint arXiv:2407.10671},
      year={2024}
}
```
