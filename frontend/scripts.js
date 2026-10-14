// JobNex Product - Client Script

const form = document.getElementById("analyze-form");
const resumeInput = document.getElementById("resume");
const jobDescriptionInput = document.getElementById("job-description");
const button = document.getElementById("analyze-button");
const statusMessage = document.getElementById("status");
const resultsSection = document.getElementById("results");
const resultData = document.getElementById("result-data");

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const resume = resumeInput.value.trim();
    const jobDescription = jobDescriptionInput.value.trim();

    if (!resume || !jobDescription) {
        statusMessage.textContent = "Please provide both Resume and Job Description.";
        return;
    }

    button.disabled = true;
    statusMessage.textContent = "Analyzing resume compatibility...";
    resultsSection.hidden = true;

    try {
        const response = await fetch("http://127.0.0.1:8000/api/analyze", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                resume_text: resume,
                jd_text: jobDescription,
                resume: resume,
                job_description: jobDescription
            })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Analysis request failed.");
        }

        resultData.textContent = JSON.stringify(data, null, 2);
        resultsSection.hidden = false;
        statusMessage.textContent = "Analysis completed successfully!";
    } catch (error) {
        statusMessage.textContent = "Error: " + error.message;
    } finally {
        button.disabled = false;
    }
});