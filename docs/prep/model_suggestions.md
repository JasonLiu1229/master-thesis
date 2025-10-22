# Model suggestions for LLM

This is a list of models that are potentially worth trying out (coding related).

## Open source

Note: while we do specify that the models are fine-tunable. We do not know if this fine-tuning will be effective for our use case.

### CodeLlama

[CodeLlama](https://huggingface.co/codellama/CodeLlama-7b-hf) is a variant built on the Llama / Llama2 family, but specialised/trained on code data. It is also available for research purposes, making it suitable for this project.

It is easy to [fine-tune](https://predibase.com/blog/how-to-efficiently-fine-tune-codellama-70b-instruct-with-predibase). With many guides on the internet.

It is also really popular, making credibility a bit higher than others. This also means that many people have worked with this model, so help is easy to find.

It also has a lightweight version of 7B parameters, making it easier for lightweight research.

### StarCoder / StarCoder2 (by BigCode)

StarCoder is an open-source code LLM trained on many programming languages and code datasets; repository: “bigcode-project/starcoder” indicates it supports [fine‐tuning](https://github.com/bigcode-project/starcoder).

This model is also very well known in the LLM comunity. This again means that there will be many tutorials online to find, in case needed.

Based online [benchmarking](https://www.labellerr.com/blog/best-coding-llms/#:~:text=StarCoder2%3A%20The%20Transparent%20Workhorse), the speed of inference is fast.

This model is slightly bigger but still manageable for human research. Here we are looking at 15B parameters.

### Codestral

[Codestral](https://huggingface.co/mistralai/Codestral-22B-v0.1) is one of the faster models we will speak of in this list. It is a model developed by Mistal AI and specificlly tailored for his speed and efficiency,

It is also [fine-tunable](https://medium.com/@aastha.code/finetuning-codestral-22b-with-qlora-locally-907062d8e15f).

It supports instruction-style usage (instruct/“chat” mode) and fill-in-the-middle (FIM) code generation (prefix + suffix → fill).

## Paid

Most of these options won't be considered, because they are paid variants. But here is a list of potential models, in case you are interested.

Note: the description will be less descriptive because it is more meant to state that paid models are also an option.

### OpenAI GPT-5

### [Claude Sonnet 4.5](https://codingscape.com/blog/best-llms-for-coding-developer-favorites#:~:text=Claude%204%20models-,Claude%20Sonnet%204.5,-Claude%20Sonnet%204.5)

### Gemini 2.5 Pro
