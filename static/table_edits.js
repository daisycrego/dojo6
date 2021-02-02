// Home page - Listings View 

// Handle updates of the most recent property value for zillow, redfin, and cb for each listing 
// Attach a click event handler to each "Edit" button in the table of values. The edit button click event
// will convert the input to a contentEditable (turning all other contentEditable inputs off) and display
// a save icon to save the new views and a cancel icon to cancel the update.

document.getElementsByName('edit-recent-value').forEach(item => {
    item.addEventListener('click', function(e) {
        
        // Parse the listing id and view_type (z, r, or c) from the current element id
        var id = e.target.id.split("_")[2];
        var view_type = e.target.id.split("_")[1];

        // Turn off all other contentEditable fields
        document.getElementsByName('recent-listing-views').forEach(item => {
            item.contentEditable = "false"; 
            item.classList.remove("input-big"); 
            item.textContent = item.textContent ? item.textContent: '-';
        })

        // Turn on all other edit icons 
        document.getElementsByName('edit-recent-value').forEach(item => {
            item.classList.remove("hidden");
        })

        // Turn off all other save icons 
        document.getElementsByName('save-recent-value').forEach(item => {
            item.classList.add("hidden");
        })

        // Turn off all other cancel icons 
        document.getElementsByName('cancel-recent-value').forEach(item => {
            item.classList.add("hidden");
        })

        // Display the save icon
        document.getElementById(`save_${view_type}_${id}`).classList.remove("hidden");

        // Display the cancel icon
        document.getElementById(`cancel_${view_type}_${id}`).classList.remove("hidden");

        // Hide the clicked icon
        e.target.classList.add("hidden");

        // Convert the value being edited to a contentEditable and resize the input
        document.getElementById(`latest_${view_type}_${id}`).contentEditable = "true";
        document.getElementById(`latest_${view_type}_${id}`).classList.add("input-big");

        console.log("HERE")
        console.log(document.getElementById(`latest_${view_type}_${id}`).textContent)

        // If the value is -, replace that with a blank
        if ('-' === document.getElementById(`latest_${view_type}_${id}`).textContent.trim()) {
            document.getElementById(`latest_${view_type}_${id}`).textContent = "";
        }
    })
})

document.getElementsByName("save-recent-value").forEach(item => {
    item.addEventListener('click', function(e) {
        var id = e.target.id.split("_")[2];
        var view_type = e.target.id.split("_")[1];

        // Move recent views to the hidden input field
        document.getElementById(`z_${id}`).value = document.getElementById(`latest_z_${id}`).textContent;
        document.getElementById(`r_${id}`).value = document.getElementById(`latest_r_${id}`).textContent;
        document.getElementById(`c_${id}`).value = document.getElementById(`latest_c_${id}`).textContent;
        document.getElementById(`update-views_${id}`).submit();
    })
});

// Listing page - Detail View 

document.querySelectorAll('p.recent-listing-views').forEach(item => {
    item.addEventListener('input', function(e) {
        // make this field into a non-contenteditable
        console.log(e);
        //e.target.contentEditable = false;
        //e.target.classList.add("input-big");
        // show save changes button (change display from hidden)
    });
})

document.getElementsByName('listing-views').forEach(item => {
    item.addEventListener('input', function(e) {
        var id = e.target.id.split('_')[2];
        document.getElementById(`edit_${id}`).classList.remove("hidden");
    })
});

function makeContentEditable(e) {
    Array.from(document.getElementsByClassName(e.id)).forEach(item => {
        item.contentEditable = "true";
        item.classList.add("input");
    });
    document.getElementById(`hide_${e.id}`).classList.remove("hidden");
    e.classList.add("hidden");
}

function hideContentEditable(e) {
    var id = e.id.split('_')[1];
    Array.from(document.getElementsByClassName(id)).forEach(item => {
        item.contentEditable = "false";
        item.classList.remove("input");
    });
    document.getElementById(`edit_${id}`).classList.add("hidden");
    document.getElementById(id).classList.remove("hidden");
    e.classList.add("hidden");
}

function submitForm(id) {
    // fill out all the hidden fields in the form and then submit it
    document.getElementById(`z_${id}`).value = document.getElementById(`z_input_${id}`).textContent;
    document.getElementById(`r_${id}`).value = document.getElementById(`r_input_${id}`).textContent;
    document.getElementById(`c_${id}`).value = document.getElementById(`c_input_${id}`).textContent;
    document.getElementById(`update-views_${id}`).submit();
}