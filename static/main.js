// Event Listeners
document.addEventListener("DOMContentLoaded", function () {
	const inputBox = document.getElementById("applicant-name");
	const form = document.getElementById("upload-form");

	inputBox.addEventListener("keypress", function (event) {
		if (event.key === "Enter") {
			event.preventDefault(); // Prevent form submission
		}
	});

	form.addEventListener("submit", function (event) {
		event.preventDefault();
	});
});

const orderedFilesInput = document.getElementById("file-order");
const successMessage = document.getElementById("success-message");
orderedFilesInput.addEventListener("change", function () {
	successMessage.classList.add("hidden");
});
applicantNameInput.addEventListener("change", function () {
	successMessage.classList.add("hidden");
});

// Functions
function updateFileList() {
	const fileInput = document.getElementById("uploaded-files");
	const fileOrderList = document.getElementById("file-order");
	const fileOrderContainer = document.getElementById("file-order-container");
	const mergeButton = document.getElementById("merge-button");
	const clearButton = document.getElementById("clear-button");

	const orderedFilesInput = document.getElementById("ordered-files");

	// Display number of files uploaded
	const countDisplay = document.getElementById("file-count");
	const files = fileInput.files;
	if (files.length === 0) {
		countDisplay.textContent = "";
	} else {
		const outputText = files.length === 1 ? " file chosen" : " files chosen";
		countDisplay.textContent = files.length + outputText;
	}
	fileOrderList.innerHTML = "";

	// Only show submit buttons if files have been uploaded
	if (files.length > 0) {
		fileOrderContainer.classList.remove("hidden");
		mergeButton.classList.remove("hidden");
		clearButton.classList.remove("hidden");
	} else {
		fileOrderContainer.classList.add("hidden");
		mergeButton.classList.add("hidden");
		clearButton.classList.add("hidden");
	}

	document.getElementById("success-message").classList.add("hidden");

	// Add delete button for each file
	for (let i = 0; i < fileInput.files.length; i++) {
		const li = document.createElement("li");
		li.textContent = fileInput.files[i].name;

		const deleteBtn = document.createElement("button");
		deleteBtn.textContent = "x";
		deleteBtn.classList.add("delete-btn");
		deleteBtn.onclick = function () {
			fileInput.files = removeFileFromFileList(
				fileInput.files,
				li.textContent.slice(0, -1)
			);

			li.remove();
			updateOrderedFilesInput();

			document.getElementById("success-message").classList.add("hidden");

			// Update file count and hide submit buttons if necessary
			const orderedFilesList = document.getElementById("ordered-files").value;

			let numFilesLeft = 0;

			if (orderedFilesList !== "") {
				numFilesLeft = orderedFilesList.split("|||").length;
			}

			const countDisplay = document.getElementById("file-count");
			if (numFilesLeft === 0) {
				countDisplay.textContent = "";
			} else {
				const outputText =
					numFilesLeft === 1 ? " file chosen" : " files chosen";
				countDisplay.textContent = numFilesLeft + outputText;
			}

			if (numFilesLeft === 0) {
				fileOrderContainer.classList.add("hidden");
				mergeButton.classList.add("hidden");
				clearButton.classList.add("hidden");
			}
		};

		li.appendChild(deleteBtn);
		li.setAttribute("data-file", fileInput.files[i].name);
		fileOrderList.appendChild(li);
	}

	Sortable.create(fileOrderList, {
		onUpdate: function () {
			updateOrderedFilesInput();
		},
	});

	updateOrderedFilesInput();
}

function removeFileFromFileList(fileList, filename) {
	const dt = new DataTransfer();
	for (let i = 0; i < fileList.length; i++) {
		if (fileList[i].name !== filename) {
			dt.items.add(fileList[i]);
		}
	}
	return dt.files;
}

function updateOrderedFilesInput() {
	const fileOrderList = document.getElementById("file-order");
	const orderedFilesInput = document.getElementById("ordered-files");
	const orderedFiles = [];
	for (let i = 0; i < fileOrderList.children.length; i++) {
		orderedFiles.push(fileOrderList.children[i].getAttribute("data-file"));
	}
	orderedFilesInput.value = orderedFiles.join("|||");
}

async function handleMerge() {
	const applicantName = document.getElementById("applicant-name").value;
	const fileInput = document.getElementById("uploaded-files");

	if (!applicantName) {
		alert("Please provide the applicant's name.");
		return;
	}

	if (fileInput.files.length === 0) {
		alert("Please upload at least one file.");
		return;
	}

	const formData = new FormData(document.getElementById("upload-form"));

	document.getElementById("feedback").innerText = "Processing...";
	document.getElementById("success-message").classList.add("hidden");

	try {
		const response = await fetch("/", {
			method: "POST",
			body: formData,
		});

		if (!response.ok) {
			const errorData = await response.json();
			const errorMessage =
				errorData.error || "There was an error with your request.";
			throw new Error(errorMessage);
		}

		const blob = await response.blob();
		const url = window.URL.createObjectURL(blob);
		const a = document.createElement("a");
		a.style.display = "none";
		a.href = url;
		a.download = `${applicantName}.pdf`;
		document.body.appendChild(a);
		a.click();
		window.URL.revokeObjectURL(url);
		document.getElementById("success-message").classList.remove("hidden");
		document.getElementById("feedback").innerText = "";
	} catch (error) {
		alert(error.message);
		document.getElementById("feedback").innerText = "";
	}
}

function clearFlashMessages() {
	const flashMessages = document.getElementById("flash-messages");
	if (flashMessages) {
		flashMessages.remove();
	}
}

function resetPage() {
	window.location.reload();
}
