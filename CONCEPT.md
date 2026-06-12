# Concept

## What shall be created

Our primary focus is the development of a carbon-optimising and carbon-aware LLM

### What does carbon optimising mean?

The LLM shall be able to generate code and optimise given code that has a reduced energy consumption and thus reduced carbon emissions.
Hereby the LLM will suggest alternative code constructs to the once presented to it. In the case of code generation it will favor greener alternatives directly.

It can also suggest refactorings such as turning off certain code paths in case they are not used very often (@Didi: Suggest we do not do that, as we need runtime data for that and this will explode the time box for the project until end of the year)

### What does carbon-aware mean?

We query the Grid Intensity API and based on that we tune the models thinking dynamically.

@Didi: Nicer would be if we can estimate the "cost" of the task and if it feels very daunting, then we rather ask more questions beforehand or suggest a smaller edit entirely.
What the model will know is how much can be saved by the fix. Depending on how big the saving is the model can say: "Currently the grid intensity is quite high, I suggest running this fix later as I can better implement it then with same carbon intensity"
Maybe we just make a line based assumption here? Or the amount of found patterns to change? -> This will naturally translate to tokens.

## What shall the AI model be able to answer

It shall guide greener software development.

It shall cater for two scenarios:
- In manual scenarios: Aiding a developer when writing or auditing code
- In automated / agent scenarios: Be able to fully engineer the greenest code for a given task

## Current state of technology

### Data sources

Many data sources that inform about general greener patterns or leaner (aka "greener") alternatives exist:

- https://patterns.greensoftware.foundation/

#### Problems

Many of the stated patterns are *often* true, but not always. Examples are:

- Use compiled languages
    - Is only true for production projects. For prototypes the time spent on the project is the main energy and carbon
      driver. Here the optimization should be for development time and not for code runtime.
- Cache Static Data
    - When data is only very rarely accessed having a cached copy locally which might need also a caching infrastructure
    can consume more energy than doing very rare network re-fetches.

Many other patterns are very debatable:
- Compress stored data
    - [Compressions costs energy](https://metrics.green-coding.io/stats.html?id=addc5f5e-55da-47f8-956d-240d06304e4e)
    Even if you never read a file again the break-even point is that you need to store the data compressed for at least
    some time before the cost of storing becomes cheaper than the initial overhead through the compression.
    - But if you either only store if for an emphemral period (minutes) compression should not be used at all.
    - Furthermore, if you read the file very often the uncompress step also comes into play and creates additional overhead.
    - The reason why still compression happens so often is that disk space was for the longest time a very finite
    resource and also disk space is typically priced by the MB in cloud environments.
    So often it is helpful financially but not necessarily environmentally.
    Also if you machines with actual installed disks, and not dynamic storage like S3 you anyway have free storage space. So
    filling that up and storing data here is essentially free and storing data becomes a whole lot cheaper.

    Example calculation for zst:
    - Assuming a 100 MB file can be compressed down to 30 MB and stored. The [cost for the compression will be about
    3.2 mWh]() and take 1 s  whereas the storage will be about
    - SSD (1000 GB) has 10 W rating. So the 100 MB file would fit 10,000 times on disk
  - SDD embodied Carbon 30 kg CO2 (Datavizta) - 4 year life time assumed => (30 / 4 / 365 / 24 / 60 / 60 / 10000)
    - Assuming 0.3 kg kg carbon per kWh
  - =>  2.378234398782344e-11 / 0.3 = 7.927447995941146e-11 kWh per second
  - `Power = 10 W / 10000 / 1000 / (60*60) = 2.777777777777778e-10 kWh per second`
  - We effectively save only 70% since we only compress-away 70 MB
  => (7.927447995941146e-11 + 2.777777777777778e-10 ) * 0.7 = 2.499365804160325e-10

  => 0.0000032 / 2.499365804160325e-10 / 60 / 60 / 24 -> 0.148 days

   With xz this becomes a different game:
   - Compression costs 150.86 mWh
   - => 0.00015086 / 2.499365804160325e-10 / 60 / 60 / 24 -> 7 days

   So although the tip can be valid, there are very many situations where it is not.

   The AI should annotate these edge cases

### Research

- Models do not produce green code by default. They can be instructuced to but only produce really good quality when certain keywords are in the prompt (e.g. optimize)
  and guidance on what exaclty shall be optimized. [(Source)](https://fount.aucegypt.edu/etds/2799/)
          - The problem here is that the developer already needs to know the patterns and methods available, which is usuall not the case
          - The root cause for this behaviour is probalby that there is no "standard response" available in the training data and the model has to reason on limited information.

- Prior work has also used a prediction pipeline to give an estimate about the total energy consumption of code [(Source)](https://sa4s-serc.github.io/encode)
    - The concept can only predict static code and delivers no heuristics as to how certain language constructs fare with variable user input.
    - In a future revision this could be integrated into the Green AI to enhance its prediciton capabilities to make a full code energy estimation
- 

### AI Models

In [earlier research](https://arxiv.org/html/2506.08790v1) AI models gave quite bad code with even officially discouraged solutions like using outdated Oracle DB Datatypes
or using memory inefficient string builder and streaming techniques.

At the time of writing (June 2026) AI models like Claude Opus 4.8 and ChatGPT 5.5 are able to already give
green recommendations when it comes to code.

For instance when planning an infrastructure an AI can already give a recommendation which is the leanest.

#### Infrastructure Example:
> I am a developing a software and decide which infrastructure to run it on. currently I am tasked to make it more secure. But I am also a very environmentally conscious. What is the overhead in terms of energy when I use a VM vs a plain Docker container?

```log
A Docker container has **very little runtime overhead** compared to bare metal because it shares the host OS kernel. 
A VM runs a **full guest OS**, so it consumes extra CPU cycles, RAM, storage, and background services.

[...]

* If you run **many small services**, containers are usually substantially more energy-efficient.
* If you need **strong isolation/security boundaries**, VMs provide better isolation but at a measurable energy cost.

[...]

VMs add non-CPU costs:

* extra RAM pressure → higher DRAM power
* hypervisor scheduling inefficiencies → CPU wakeups
* duplicated OS background processes
* worse consolidation (fewer workloads per host → higher idle power per workload)

[...]

At high server utilization:

* CPU overhead ≈ energy overhead (closer alignment)
At low/moderate utilization (common in real systems): * energy overhead can be **2–3× the CPU overhead difference**

### Bottom line

* CPU overhead difference: single-digit % (containers) vs up to ~25% (VMs)
* Energy overhead difference: typically **~5–30% more energy per workload for VMs**, often exceeding CPU delta due to memory + underutilization effects

> Response by ChatGPT 5.4
```

So one can see that an LLM can not only provide background information why a technology should be theoretically
be less energy consuming, but also can give ballpark numbers why that is the case.

The data actually corresponds to our internal measurements on [Docker vs. VMs](https://metrics.green-coding.io/compare.html?ids=68fb8502-4a61-40b8-a5cd-14bb7affda4b,e9289785-98bf-4e81-8069-b494fdaa00ba,98265e98-8126-4f72-8f1b-bc7ecd1892c5,cd83a76e-fa24-4317-a107-50e84d5a5cc7,0ddc51b2-e75b-45c7-9b73-34611063d8e6,d4d4441b-b1a8-426b-8ce9-c6636640853f,d1c4f8b0-0093-40b6-a27e-47f9056f0569&force_mode=usage_scenarios)

#### Image Rendering Example
However for image rendering, a more niche topic, the results are vague and unhelpful:

> I am a web developer and want to recommend image formats to my clients to use. Hereby I want to list the image formats according to their rendering cost in the browser (decoding and displaying them). Can you rank these image formats for me.
>  Please ignore encoding costs in your response.

```
Ranking from lowest to highest decode/render cost in the browser:

- BMP – Uncompressed, no decode work beyond reading raw pixels. Cheapest to decode (but huge file size).
- GIF – Simple LZW decompression; very lightweight, especially for static images. Animation adds frame-management overhead.
- PNG – DEFLATE decompression plus unfiltering. Lossless, moderate cost; rises with alpha and large dimensions.
- JPEG – DCT-based decode (entropy decode, dequantize, inverse DCT, upsampling). Well-optimized and hardware-accelerated in most browsers, but more arithmetic than PNG.
- WebP – Two modes: lossy is roughly VP8 intra-frame decoding (heavier than JPEG); lossless is more complex than PNG. Generally costlier than JPEG.
- AVIF – AV1 intra-frame decoding. Excellent compression but the most computationally expensive to decode of the common web formats; least hardware-accelerated.

A few caveats worth passing to clients:
- actual cost depends heavily on image dimensions (pixel count usually dominates), not just format.
- Hardware acceleration availability varies by browser and device, which can reorder JPEG/WebP/AVIF in practice.
- And the smaller file sizes of WebP/AVIF reduce network and memory pressure, which often outweighs their higher CPU decode cost overall.

For most clients the practical recommendation is AVIF or WebP with a JPEG/PNG fallback, since the bandwidth savings typically matter more than raw decode time.

> Response by Claude Opus 4.8 with High Effort Thinking
```

The [result in benchmarks](https://metrics.green-coding.io/stats.html?id=d77a7951-be7f-4d01-b021-e488b1969361) however is quite different:

- JPG
- webp
- AVIF
- GIF
- PNG


#### Generation Case

Given a code case the AI often prefers the "statisitically most likely" response over the leanest one as simply more of the former
is in the training data

**Example**:
> Please generate me a sample portfolio website for a client with 10 pictures. 5 Above the fold and five below.

#### Optimization Case

If a code sample is presented the AI often does not choose the leanest path by default

**Example:**
> Please look at this code and optimize it for reduced energy consumption and carbon emissions
>

Please generate me a code which does the following in python
- Make a loop with some calculations in it and a database query in it
- Send an email to the client in every step of the loop
- Import something from python with *
- Use a regex in the loop to match something as a condition
- have a quuite complex if statement with 10 if elif branches

### Resolve

So in essence the Green AI shall innovate in two fields:
- Give validated responses based on most current measurement data. Always freshyl updated by a skill / retraining
- Optimize given code to the lowest possible mean better than current models
- Ask follow up questions to validate cut-off points as some recommendations only apply in certain scenarios of the code
    - Prototype mode: Just shell out the smallest working code and force model to actually ignore best practices of caching etc. as they provide no value here
    and prefer short responses to save tokens
    - Production mode: Apply most effort to write leanest code possible given infused knowledge

Assuming you would build a web page and have to decide on a multi-dimensional optimization problem:
- Optimize Images
- Change Delivery protocal from HTTP/1.1 to HTTP/2.0
- Apply Lazy Loading
- Change JS Transformations to CSS

But you can choose only one. Which would you choose if you do not have concrete data on how much each saving can yield?

Assuming I have 100 images on the page and 70 transformations



### Solving Complex AI Queries

> assuming I have a 100 MB file which I can compress to about 70 MB. Is it better in terms of carbon saving to compress the file and store it compressed, or to not compress it and store it uncompressed. Please consider embodied carbon of a disk and also energy cost of storage on a disk. You may assume the disk is used for 4 years, can store 1 TB and takes 30 kg of carbon to create. The disk will use 10 W constant power. Please fractionalize the share of the 100 MB on the full disk for power and carbon. As a result I want the break-even point in seconds when cost for storing the compressed copy and having it compressed one time is equal to never compressiong in the first place but storing it uncompressed

This is something that no current AI model can solve properly. They always falter at some point of the mathematical 
formula.
Here we are not skilled enough to make this better. The only way would be a RAG to get the correct results but then it
would be limited to a certain kind of calculation only.


## Output

A developer should get the following informations:

- Making this particular change can save you x mWh per execution. When having this functionality
for instance executed in a FaaS with 10.000 invocations a day this would save x mWh per year

- Also the user should get the info: When applying ALL recommendations for this file the total savings would
be x mWh. This should be so the user can decide if the costs really outweigh the change overhead done
by for instance an LLM model

