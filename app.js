const stages = Array.from(document.querySelectorAll(".agent-node"));
const runButton = document.querySelector("#runPipeline");

const stageTimings = [
  "Intent object formed",
  "World details filtered",
  "Rhythm arc drafted",
  "Discovery selected",
  "Resonance found",
  "Voice calibrated",
  "Crossword generated",
  "Letter composed",
];

function setStage(index) {
  stages.forEach((stage, stageIndex) => {
    stage.classList.toggle("complete", stageIndex < index);
    stage.classList.toggle("active", stageIndex === index);
  });

  if (index >= stages.length) {
    runButton.textContent = "Run simulation";
    runButton.disabled = false;
    return;
  }

  runButton.textContent = stageTimings[index];
}

function runPipeline() {
  runButton.disabled = true;
  let index = 0;
  setStage(index);

  const interval = window.setInterval(() => {
    index += 1;
    setStage(index);

    if (index >= stages.length) {
      window.clearInterval(interval);
    }
  }, 650);
}

runButton.addEventListener("click", runPipeline);
