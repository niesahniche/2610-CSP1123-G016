const form = document.getElementById('addForm');
const input = document.getElementById('itemInput');
const list = document.getElementById('groceryList');

// Handle manual form submission
form.addEventListener('submit', function(event) {
event.preventDefault();
const value = input.value.trim();
if (value !== "") {
addItem(value);
input.value = "";
input.focus();
}
});

// Function to add item
function addItem(name) {
const li = document.createElement('li');
li.textContent = name;

const removeBtn = document.createElement('button');
removeBtn.textContent = "✖";
removeBtn.onclick = function() {
list.removeChild(li);
};

li.appendChild(removeBtn);
list.appendChild(li);
}

