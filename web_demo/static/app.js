const form = document.querySelector("#generateForm");
const sourceText = document.querySelector("#sourceText");
const sourceFile = document.querySelector("#sourceFile");
const exampleSelect = document.querySelector("#exampleSelect");
const generateButton = document.querySelector("#generateButton");
const clearButton = document.querySelector("#clearButton");
const downloadButton = document.querySelector("#downloadButton");
const message = document.querySelector("#message");
const factsPanel = document.querySelector("#factsPanel");
const factsOutput = document.querySelector("#factsOutput");
const sourceDescription = document.querySelector("#sourceDescription");
const outputsGrid = document.querySelector("#outputsGrid");
const outputTemplate = document.querySelector("#outputTemplate");

const outputTitles = {
  blog: "Blog Post",
  linkedin: "LinkedIn Post",
  tweet_thread: "Tweet Thread",
  newsletter: "Newsletter Section",
};

let examples = [];
let lastMarkdown = "";

function setMessage(text, type = "") {
  message.textContent = text;
  message.className = `message ${type}`.trim();
}

function resetResults() {
  lastMarkdown = "";
  downloadButton.disabled = true;
  factsPanel.classList.add("hidden");
  factsOutput.textContent = "";
  sourceDescription.textContent = "";
  outputsGrid.innerHTML = "";
}

function renderChecks(container, validation) {
  container.innerHTML = "";
  validation.checks.slice(0, 4).forEach((check) => {
    const badge = document.createElement("span");
    badge.className = check.ok ? "check" : "check warning";
    badge.textContent = check.message;
    container.appendChild(badge);
  });
}

function renderOutput(key, output) {
  const fragment = outputTemplate.content.cloneNode(true);
  const card = fragment.querySelector(".output-card");
  const title = fragment.querySelector("h3");
  const metric = fragment.querySelector(".metric");
  const pre = fragment.querySelector("pre");
  const checks = fragment.querySelector(".checks");

  title.textContent = outputTitles[key] || key;
  metric.textContent = `${output.validation.word_count} palavras`;
  pre.textContent = output.text;
  renderChecks(checks, output.validation);

  outputsGrid.appendChild(card);
}

function renderResults(data) {
  lastMarkdown = data.markdown;
  downloadButton.disabled = false;
  factsPanel.classList.remove("hidden");
  factsOutput.textContent = data.facts;
  sourceDescription.textContent = data.source_description;
  outputsGrid.innerHTML = "";

  Object.entries(data.outputs).forEach(([key, output]) => {
    renderOutput(key, output);
  });

  setMessage("Conteudos gerados pelo agente.", "success");
}

async function loadExamples() {
  const response = await fetch("/api/examples");
  if (!response.ok) {
    return;
  }

  const data = await response.json();
  examples = data.examples || [];
  examples.forEach((example, index) => {
    const option = document.createElement("option");
    option.value = String(index);
    option.textContent = example.label;
    exampleSelect.appendChild(option);
  });
}

exampleSelect.addEventListener("change", () => {
  const example = examples[Number(exampleSelect.value)];
  if (!example) {
    return;
  }

  sourceText.value = example.content;
  sourceFile.value = "";
  resetResults();
  setMessage(`Exemplo carregado: ${example.filename}`);
});

clearButton.addEventListener("click", () => {
  sourceText.value = "";
  sourceFile.value = "";
  exampleSelect.value = "";
  resetResults();
  setMessage("Envia uma fonte para o agente gerar os formatos.");
});

downloadButton.addEventListener("click", () => {
  if (!lastMarkdown) {
    return;
  }

  const blob = new Blob([lastMarkdown], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "content_pipeline_outputs.md";
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  resetResults();
  setMessage("A processar a fonte. Isto pode demorar alguns segundos.");
  generateButton.disabled = true;
  generateButton.textContent = "A gerar...";

  try {
    const formData = new FormData(form);
    const response = await fetch("/api/generate", {
      method: "POST",
      body: formData,
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || "Ocorreu um erro ao gerar os conteudos.");
    }

    renderResults(data);
  } catch (error) {
    setMessage(error.message, "error");
  } finally {
    generateButton.disabled = false;
    generateButton.textContent = "Gerar conteudos";
  }
});

loadExamples();
