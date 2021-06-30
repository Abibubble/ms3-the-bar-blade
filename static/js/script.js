// -------------------------------------------------------------------- Materialize

$(document).ready(function(){ // jQuery sections from Materalize
    $('.sidenav').sidenav({edge: "right"});
    $('.collapsible').collapsible();
    $('select').formSelect();

    validateMaterializeSelect(); // jQuery Select validation from the Code Institute task manager mini-project
    function validateMaterializeSelect() {
        let classValid = { "border-bottom": "1px solid #4caf50", "box-shadow": "0 1px 0 0 #4caf50" };
        let classInvalid = { "border-bottom": "1px solid #f44336", "box-shadow": "0 1px 0 0 #f44336" };
        if ($("select.validate").prop("required")) {
            $("select.validate").css({ "display": "none", "height": "0", "padding": "0", "width": "0", "position": "absolute" });
        }
        $(".select-wrapper input.select-dropdown").on("focusin", function () {
            $(this).parent(".select-wrapper").on("change", function () {
                if ($(this).children("ul").children("li.selected:not(.disabled)").on("click", function () { })) {
                    $(this).children("input").css(classValid);
                }
            });
        }).on("click", function () {
            if ($(this).parent(".select-wrapper").children("ul").children("li.selected:not(.disabled)").css("background-color") === "rgba(0, 0, 0, 0.03)") {
                $(this).parent(".select-wrapper").children("input").css(classValid);
            } else {
                $(".select-wrapper input.select-dropdown").on("focusout", function () {
                    if ($(this).parent(".select-wrapper").children("select").prop("required")) {
                        if ($(this).css("border-bottom") != "1px solid rgb(76, 175, 80)") {
                            $(this).parent(".select-wrapper").children("input").css(classInvalid);
                        }
                    }
                });
            }
        });
    }
});

// -------------------------------------------------------------------- Add Ingredients

let counter = 2;
let max = 20;

let newIngredient = `<div class="row" id="addIngredient-*"><div class="input-field col s10 m8 offset-s1 offset-m2">
<i class="fas fa-mortar-pestle prefix"></i>
<input id="recipe_list" name="recipe_list" type="text" minlength="5" maxlength="100" class="validate white-text" required>
<label for="recipe_list"></label>
<a class="waves-effect waves-light btn" onClick="deleteIngredient(this)" data-ingredient="ingredient-*"><i class="fas fa-times"></i> Remove</a>
</div></div>`;

function addIngredient(add) {
    if (counter === max) {
        alert("You have reached the maximum amount of ingredients");
    } else {
        console.log("Adding Ingredient");
        newIngredient = newIngredient.replaceAll("*", counter);
        document.getElementById(add).insertAdjacentHTML('beforebegin', newIngredient);
        counter++;
    }
};

// -------------------------------------------------------------------- Copyright

function copyrightYear() {
    var d = new Date();
    var y = d.getFullYear();
    document.getElementById("copyright").innerHTML = y;
}

copyrightYear();