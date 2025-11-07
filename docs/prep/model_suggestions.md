# Model suggestions for LLM

This is a list of models that are potentially worth trying out (coding related).

## Open source

Note: while we do specify that the models are fine-tunable. We do not know if this fine-tuning will be effective for our use case.

### CodeLlama

[CodeLlama](https://huggingface.co/codellama/CodeLlama-7b-hf) is a variant built on the Llama / Llama2 family, but specialised/trained on code data. It is also available for research purposes, making it suitable for this project.

It is easy to [fine-tune](https://predibase.com/blog/how-to-efficiently-fine-tune-codellama-70b-instruct-with-predibase). With many guides on the internet.

It is also really popular, making credibility a bit higher than others. This also means that many people have worked with this model, so help is easy to find.

It also has a lightweight version of 7B parameters, making it easier for lightweight research.

It inherits LLaMA architecture improvements. This means it includes several like optimizations made by LLaMA.

It also has a high code reasoning aspect, could mean that naming tasks are easier because it reasons over it.

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

## Selected model (OS)

The selection of CodeLlama as the foundational model for this research is motivated by three central considerations: scientific reproducibility, architectural suitability for code comprehension tasks, and practical feasibility for controlled experimentation.

First, CodeLlama is fully open source, which ensures that every stage of the research pipeline—including preprocessing, fine-tuning, inference, and evaluation—can be reproduced and independently validated. This level of transparency is critical for academic work and cannot be guaranteed when using proprietary large language models that do not disclose their training data, architecture details, or model weights.

Second, CodeLlama is specifically optimized for programming-related tasks. Its training corpus, tokenizer configuration, and instruction-tuned variants are designed to model the syntactic and semantic structures of source code more effectively than general-purpose language models. This specialization aligns directly with the objectives of this thesis, which focuses on improving the understandability of test code and generating or refining identifier names. The model’s strong baseline performance on established coding benchmarks provides a reliable foundation for investigating the incremental effects of fine-tuning.

Finally, CodeLlama benefits from a mature ecosystem of fine-tuning frameworks, documentation, and community support. This facilitates efficient experimentation and reduces engineering overhead, allowing the research to focus on methodological rigor rather than model-integration challenges. Moreover, the availability of multiple model sizes enables controlled comparisons without altering the underlying architecture, improving the internal validity of the experimental design.

For these reasons, CodeLlama represents a technically robust, scientifically transparent, and practically feasible choice for conducting research on machine learning-based improvements to test code understandability.
