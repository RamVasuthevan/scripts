// Function to load JSON data and populate the grid
async function loadJSON() {
    try {
        const response = await fetch('data.json');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        data.forEach(item => {
            addRow(item);
        });
    } catch (error) {
        console.error("Error loading JSON:", error);
    }
}

// Function to add a new row
function addRow(data = { url: '', author: '', title: '', notes: '', tags: [] }) {
    const container = document.querySelector('.container');

    const urlDiv = document.createElement('div');
    const authorDiv = document.createElement('div');
    const titleDiv = document.createElement('div');
    const notesDiv = document.createElement('div');
    const tagsDiv = document.createElement('div');
    const actionsDiv = document.createElement('div');

    urlDiv.textContent = data.url;
    authorDiv.textContent = data.author;
    titleDiv.textContent = data.title;
    
    // Replace newlines with <br> for rendering
    notesDiv.innerHTML = data.notes.replace(/\n/g, '<br>');
    
    tagsDiv.textContent = Array.isArray(data.tags) ? data.tags.join(', ') : ''; 

    actionsDiv.innerHTML = '<button class="delete-btn" onclick="deleteRow(this)">Delete</button>';

    container.appendChild(urlDiv);
    container.appendChild(authorDiv);
    container.appendChild(titleDiv);
    container.appendChild(notesDiv);
    container.appendChild(tagsDiv);
    container.appendChild(actionsDiv);
}

// Function to enable in-place editing
function enableEditing(event) {
    const target = event.target;

    // Prevent editing on header cells or delete buttons
    if (target.classList.contains('header') || target.tagName.toLowerCase() === 'button') {
        return;
    }

    const initialValue = target.textContent.trim();
    const input = document.createElement('textarea');
    input.value = initialValue.replace(/<br>/g, '\n'); // Revert <br> to newline for editing

    target.innerHTML = '';
    target.appendChild(input);
    input.focus();

    input.addEventListener('blur', function() {
        const newValue = input.value.trim();
        if (target === target.parentElement.children[4]) { // Tags column
            target.textContent = newValue.split(',').map(tag => tag.trim()).join(', ');
        } else {
            // Replace newlines with <br> for rendering
            target.innerHTML = newValue.replace(/\n/g, '<br>') || initialValue;
        }
    });

    input.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            input.blur();
        }
    });
}

// Function to delete a row
function deleteRow(button) {
    const container = document.getElementById('gridContainer');
    const allCells = Array.from(container.children);
    const index = allCells.indexOf(button.parentElement);
    const columns = 6; // Total number of columns

    for (let i = 0; i < columns; i++) {
        container.removeChild(allCells[index - i]);
    }
}

// Function to copy the JSON data
function copyJSON() {
    const container = document.getElementById('gridContainer');
    const allCells = Array.from(container.children);
    const columns = 6; // Total number of columns
    const data = [];

    for (let i = columns; i < allCells.length; i += columns) { // Skip headers
        data.push({
            url: allCells[i].textContent,
            author: allCells[i + 1].textContent,
            title: allCells[i + 2].textContent,
            notes: allCells[i + 3].innerHTML.replace(/<br>/g, '\n'), // Revert <br> to newline for JSON
            tags: allCells[i + 4].textContent.split(',').map(tag => tag.trim())
        });
    }

    const jsonString = JSON.stringify(data, null, 2);

    const tempTextArea = document.createElement('textarea');
    tempTextArea.value = jsonString;
    document.body.appendChild(tempTextArea);
    tempTextArea.select();
    document.execCommand('copy');
    document.body.removeChild(tempTextArea);

    const copyButton = document.querySelector('.copy-json-btn');
    copyButton.textContent = 'Copied!';
    setTimeout(() => {
        copyButton.textContent = 'Copy JSON';
    }, 2000);
}

// Add double-click event listener to all cells for editing
document.getElementById('gridContainer').addEventListener('dblclick', enableEditing);

// Load the JSON data when the page loads
window.onload = loadJSON;
