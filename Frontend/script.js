async function analyze() {
  const reviewText = document.getElementById("review").value;
  const rating = Number(document.getElementById("rating").value);
  const output = document.getElementById("output");

  output.innerHTML = "Analyzing...";

  try {
    const response = await fetch("http://127.0.0.1:8000/analyze", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        review_text: reviewText,
        rating: rating,
        image: null,
      }),
    });

    if (!response.ok) {
      throw new Error("API error");
    }

    const data = await response.json();

    output.innerHTML = `
      <h3>Result</h3>
      <p><b>Risk:</b> ${data.risk_level}</p>
      <p><b>Confidence:</b> ${data.confidence}%</p>
      <ul>
        ${data.reasons.map(r => `<li>${r}</li>`).join("")}
      </ul>
    `;
  } catch (err) {
    output.innerHTML = `<p style="color:red;">Failed to analyze review</p>`;
  }
}