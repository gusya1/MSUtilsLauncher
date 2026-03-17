    window.onload = init;

    function init(){
        var button = document.getElementById("addBtn_dictfield_1");
        button.onclick = handleButtonClick;
    }

    function createNewRow() {
        var row = document.createElement("tr");

        row.appendChild();
    }

    function handleButtonClick() {
        var table = document.getElementById("table_dictfield_1");
        table.appendChild(document.createTextNode("<td><input/></td><td><input/></td><td><button>Trash</button></td>"));
    }
