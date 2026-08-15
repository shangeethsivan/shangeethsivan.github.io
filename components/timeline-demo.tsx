import React from "react";
import { Timeline } from "@/components/ui/timeline";

export function TimelineDemo() {
  const data = [
    {
      title: "1940s – 1950s",
      content: (
        <div>
          <p className="text-neutral-800 dark:text-neutral-200 text-sm md:text-base font-normal mb-8">
            <strong>Early Foundations & Claude Shannon:</strong> McCulloch & Pitts (1943) proposed mathematical neural nets, Alan Turing published machine intelligence tests (1950), and Claude & Betty Shannon proved human language has statistical redundancy via next-letter prediction.
          </p>
          <div className="grid grid-cols-2 gap-4">
            <img
              src="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=600&q=80"
              alt="Neural networks conceptual abstract"
              width={500}
              height={500}
              className="rounded-lg object-cover h-20 md:h-44 lg:h-60 w-full shadow-lg"
            />
            <img
              src="https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?auto=format&fit=crop&w=600&q=80"
              alt="Binary data matrix code"
              width={500}
              height={500}
              className="rounded-lg object-cover h-20 md:h-44 lg:h-60 w-full shadow-lg"
            />
          </div>
        </div>
      ),
    },
    {
      title: "1960s – 1990s",
      content: (
        <div>
          <p className="text-neutral-800 dark:text-neutral-200 text-sm md:text-base font-normal mb-8">
            <strong>Symbolic AI & Backpropagation:</strong> Early natural language chatbots like ELIZA (1966) used hardcoded pattern matching rules. In 1986, Rumelhart, Hinton, and Williams popularized backpropagation, enabling multi-layer neural network optimization.
          </p>
          <div className="grid grid-cols-2 gap-4">
            <img
              src="https://images.unsplash.com/photo-1550751827-4bd374c3f58b?auto=format&fit=crop&w=600&q=80"
              alt="Retro technology circuit board"
              width={500}
              height={500}
              className="rounded-lg object-cover h-20 md:h-44 lg:h-60 w-full shadow-lg"
            />
            <img
              src="https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=600&q=80"
              alt="Microchip circuit board"
              width={500}
              height={500}
              className="rounded-lg object-cover h-20 md:h-44 lg:h-60 w-full shadow-lg"
            />
          </div>
        </div>
      ),
    },
    {
      title: "2017 – 2026",
      content: (
        <div>
          <p className="text-neutral-800 dark:text-neutral-200 text-sm md:text-base font-normal mb-4">
            <strong>Transformer Revolution & Streaming LLMs:</strong> The 2017 "Attention Is All You Need" paper replaced recurrent neural nets. Modern LLMs predict sub-word tokens at scale, streaming real-time responses to user prompts across OpenRouter APIs.
          </p>
          <div className="mb-8 flex flex-col gap-2 text-neutral-700 dark:text-neutral-300 text-xs md:text-sm font-mono">
            <div>✅ Self-Attention Transformer Architectures</div>
            <div>✅ Web-scale Pre-training & RLHF Alignment</div>
            <div>✅ OpenRouter Multi-Model Unified APIs</div>
            <div>✅ Real-Time Token Streaming on Mobile & Web</div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <img
              src="https://images.unsplash.com/photo-1677442136019-21780efad99a?auto=format&fit=crop&w=600&q=80"
              alt="Artificial Intelligence brain graphic"
              width={500}
              height={500}
              className="rounded-lg object-cover h-20 md:h-44 lg:h-60 w-full shadow-lg"
            />
            <img
              src="https://images.unsplash.com/photo-1620712943543-bcc4688e7485?auto=format&fit=crop&w=600&q=80"
              alt="Deep learning network"
              width={500}
              height={500}
              className="rounded-lg object-cover h-20 md:h-44 lg:h-60 w-full shadow-lg"
            />
          </div>
        </div>
      ),
    },
  ];

  return (
    <div className="min-h-screen w-full bg-black text-white">
      <Timeline data={data} />
    </div>
  );
}
