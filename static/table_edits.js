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