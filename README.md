# Mini-Boss: Auto-GPT Orchestrator for Scalable AI-powered Task Management
[![GitHub Repo stars](https://img.shields.io/github/stars/MiniBossGPT/Mini-Boss?style=social)](https://github.com/MiniBossGPT/Mini-Boss/stargazers)
[![Twitter Follow](https://img.shields.io/twitter/follow/minibossgpt?style=social)](https://twitter.com/MiniBossGPT)

<p align="center">
  <img src="https://raw.githubusercontent.com/MiniBossGPT/Mini-Boss/master/images/DALE_2_MINI_BOSS.PNG" width="60%" height="60%">
</p>



## 💡 Get help - [Q&A](https://github.com/MiniBossGPT/Mini-Boss//discussions/categories/q-a)

<hr/>


Mini-Boss is an innovative open-source project that harnesses the power of the GPT-4 language model and Auto-GPT (https://github.com/Significant-Gravitas/Auto-GPT). Leveraging Auto-GPT on the foundation of GPT-4, this application seamlessly connects LLM "thoughts" to autonomously accomplish any objective you define. As an early example of fully autonomous GPT-4 implementation, Mini-Boss is redefining the frontiers of AI capabilities.
<h2 align="center"> Demo May 11rd 2023 </h2>


<p align="center">
  <img src="https://raw.githubusercontent.com/MiniBossGPT/Mini-Boss/master/images/console_example_3.png" width="90%" height="90%">
</p>


<h2 align="center"> Demo May 5rd 2023 </h2>


<p align="center">
  <img src="https://raw.githubusercontent.com/MiniBossGPT/Mini-Boss/master/images/console_example_2.png" width="90%" height="90%">
</p>


<h2 align="center"> Demo May 3rd 2023 </h2>


<p align="center">
  <img src="https://raw.githubusercontent.com/MiniBossGPT/Mini-Boss/master/images/console_example.png" width="90%" height="90%">
</p>


<h2 align="center"> 💖 Help Fund Mini-Boss's Development 💖</h2>
<p align="left">
If you can spare a coffee, you can help to cover the costs of developing Mini-Boss and help to push the boundaries of fully autonomous AI!
Your support is greatly appreciated. Development of this free, open-source project is made possible by all the <a href="https://github.com/MiniBossGPT/Mini-Boss//graphs/contributors">contributors</a> and <a href="https://github.com/sponsors/MiniBossGPT">sponsors</a>. If you'd like to sponsor this project and have your avatar or company logo appear below <a href="https://github.com/sponsors/MiniBossGPT">click here</a>.

Your support goes a long way in advancing Mini-Boss and pushing the limits of fully autonomous AI! If you can contribute the cost of a coffee, you'll be helping to cover development expenses and enabling us to continue creating this free, open-source project. Every contribution makes a difference, and we're truly grateful for your generosity.

By sponsoring Mini-Boss, you'll be recognized as a driving force behind this innovative project. Click <a href="https://github.com/sponsors/MiniBossGPT">here</a> to become a sponsor and have your avatar or company logo featured below, showcasing your invaluable support for the development of Mini-Boss.
</p>



## 🚀 Features

1. 🎯 **Intelligent Work Plan Generation** 
   - By creating a top-level GPT-4 LLM instance called MiniBoss, users can submit their plan. MiniBoss utilizes LLM to generate an actionable work plan, incorporating the first memory separation to prevent context and history loss due to token limits.  
2. 🤝 **Buddy System Integration** 
   - MiniBoss launches a Buddy (a second GPT-4 LLM instance) to handle the assigned job. The Buddy then initiates a subprocess of Auto-GPT, fully integrating the Auto-GPT ecosystem.  
3. 🔗 **Direct Auto-GPT Interaction** 
   - Users interact directly with Auto-GPT. Once Auto-GPT completes the task and shuts down, control reverts to the Buddy, which employs LLM for self-reflection and self-assessment of the output.  
4. 📊 **Result Evaluation and Reassignment** 
   - Upon task completion, the Buddy notifies MiniBoss, which then reflects on the result and assigns a score or grade. If the score fails to meet the preconfigured threshold, MiniBoss launches a new Buddy for the same job.  
5. 🧵 **Multithreading with Auto-GPT Continuous Mode (In Progress)** 
   - The system will introduce multithreading to work with Auto-GPT in continuous mode, enabling the launch of multiple workers and selection of the best results.  
6. ⏭️ **Sequential Task Completion** 
   - When MiniBoss determines that a Buddy has successfully completed the task, it launches a new Buddy for the next job in the sequence.  
7. 🔄 **Feedforward Mechanism** 
   - The successful Buddy's job result and self-reflection are passed to the next worker, creating a forward feedback loop until all jobs assigned to MiniBoss are completed.  
8. 🔍 **Final Analysis (In Progress)** 
   - Work is currently underway to develop the final analysis component of the system.


## Notes from Asad K. (Mini-Boss Co-Creator)

* 🌐 **A High-Level Management Layer**

> Mini-Boss serves as an advanced management layer, acting as a centralized and focused agent overseeing AutoGPT's operations. It ensures all sub-tasks and sub-agents remain on track, producing results aligned with the overall goal. This 'mini-boss' plays a crucial role in managing AutoGPT's complexity, preventing any deviation from the main objective.

* 🎯 **Improved Accuracy and Focus**

> Mini-Boss enhances AutoGPT's output accuracy by providing higher-level oversight. The focused management layer guarantees each sub-task generated by the model is relevant and contributes to the end goal, resulting in more coherent and accurate responses from AutoGPT.

* 🔍 **Result Analysis**

> A key feature of Mini-Boss is its built-in result analysis capability. This tool enables Mini-Boss to assess each sub-agent's output, verifying the relevance and accuracy of their responses. By analyzing results, Mini-Boss adjusts sub-agents' direction, guiding them back on track if needed. This feature not only improves AutoGPT's output quality but also strengthens the model's self-awareness, enhancing its ability to self-correct and maintain focus.

* 🧠 **A Layer of Self-Awareness**

> One of Mini-Boss's most groundbreaking aspects is the added layer of self-awareness to AutoGPT. By evaluating sub-agents' output, Mini-Boss detects when the model strays from the task at hand. This self-awareness empowers the model to self-correct, refocusing efforts on the intended goal. It marks a significant step forward in developing more sophisticated and reliable AI models.




## Quickstart

1. Get an OpenAI [API Key](https://platform.openai.com/account/api-keys)
2. Download the [latest release](https://github.com/MiniBossGPT/Mini-Boss//releases/latest)
3. Follow the [installation instructions][docs/setup]
4. Configure any additional features from Auto-GPT-Plugins if you want, or install some [plugins][docs/plugins]
5. [Run][docs/usage] the app

Please see the [documentation][docs] for full setup instructions and configuration options.


## 📖 Documentation
* [⚙️ Setup][docs/setup]
* [💻 Usage][docs/usage]
* [🔌 Plugins][docs/plugins]
* Configuration
  * [🧠 Auto-GPT](https://github.com/Significant-Gravitas/Auto-GPT)


[docs]: https://github.com/MiniBossGPT/Mini-Boss/blob/master/docs/index.md
[docs/setup]: https://github.com/MiniBossGPT/Mini-Boss/blob/master/docs/setup.md
[docs/usage]: https://github.com/MiniBossGPT/Mini-Boss/blob/master/docs/usage.md
[docs/plugins]: https://github.com/MiniBossGPT/Mini-Boss/blob/master/docs/plugins.md


## ⚠️ Limitations

This experiment aims to showcase the potential of management for autonomous Auto-GPT agents utilizing GPT-4 but comes with some limitations:

1. Not a polished application or product, just an experiment
2. May not perform well in complex, real-world business scenarios. In fact, if it actually does, please share your results!
3. Quite expensive to run, so set and monitor your API key limits with OpenAI!


## 🌟 Meet the Creators and Acknowledgements

**John H.** - Co-Creator

Hi, I'm John H., and I am a Principal Software Architect and I've had the pleasure of co-creating the Mini-Boss project. I'm passionate about AI and constantly exploring new ways to push the boundaries of what's possible with this technology.

**Asad K.** - Co-Creator

A huge shoutout to my co-creator, Asad K., whose insights, dedication, and hard work have been invaluable in shaping Mini-Boss into the innovative project it is today.

**Special Thanks to the Auto-GPT Team** - [Auto-GPT](https://github.com/Significant-Gravitas/Auto-GPT)

We'd like to extend our deepest gratitude to the brilliant minds behind Auto-GPT. Their work has inspired and enabled the development of Mini-Boss, and we couldn't have done it without them. Thank you for your incredible contribution to the AI community!



## 🛡 Disclaimer

This project, Mini-Boss, is an experimental application and is provided "as-is" without any warranty, express or implied. By using this software, you agree to assume all risks associated with its use, including but not limited to data loss, system failure, or any other issues that may arise.

The developers and contributors of this project do not accept any responsibility or liability for any losses, damages, or other consequences that may occur as a result of using this software. You are solely responsible for any decisions and actions taken based on the information provided by Mini-Boss.

**Please note that the use of the GPT-4 language model can be expensive due to its token usage.** By utilizing this project, you acknowledge that you are responsible for monitoring and managing your own token usage and the associated costs. It is highly recommended to check your OpenAI API usage regularly and set up any necessary limits or alerts to prevent unexpected charges.

As an autonomous experiment, Mini-Boss may generate content or take actions that are not in line with real-world business practices or legal requirements. It is your responsibility to ensure that any actions or decisions made based on the output of this software comply with all applicable laws, regulations, and ethical standards. The developers and contributors of this project shall not be held responsible for any consequences arising from the use of this software.

By using Mini-Boss, you agree to indemnify, defend, and hold harmless the developers, contributors, and any affiliated parties from and against any and all claims, damages, losses, liabilities, costs, and expenses (including reasonable attorneys' fees) arising from your use of this software or your violation of these terms.

## 🐦 Connect with Us on Twitter

Stay up-to-date with the latest news, updates, and insights about Mini-Boss by following our Twitter accounts. Engage with the developer and the AI's own account for interesting discussions, project updates, and more.

- **All**: Follow [@minibossgpt](https://twitter.com/minibossgpt) for insights into the development process, project updates, and related topics from the creator of Entrepreneur-GPT.

We look forward to connecting with you and hearing your thoughts, ideas, and experiences with Mini-Boss. Join us on Twitter and let's explore the future of AI together!

<p align="center">
  <a href="https://star-history.com/#MiniBossGPT/mini-boss&Date">
    <img src="https://api.star-history.com/svg?repos=MiniBossGPT/mini-boss&type=Date" alt="Star History Chart">
  </a>
</p>
