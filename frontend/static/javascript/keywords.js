$(document).ready(function () { //TODO remove this is for testing only
    var keywords = ["pepsi1jasndjsndjsfjdjsafjdbsfjhb","pepsi2","pepsi3","pepsi4","pepsi5","pepsi6","pepsi7","pepsi8","pepsi9","pepsi10","pepsi11"] //TODO add input arg and remove list
    $.each(keywords, show_keyword);
});

function show_keyword(index,keyword){
    var keyword_list = $("#keywords");
    if(keyword_list.children().length >= 8){
        return 0
    }
    var new_keyword_element = $("<div class='keyword'></div>");
    var buttons = $("<div class='keyword_buttons'></div>");
    var add_button = $("<div class='add_keyword glyphicon glyphicon-ok' data-value='keyword' title='Add this keyword to list' onclick='add_keyword(this)' style='color:green; cursor:pointer;'></div>");
    var discard_button = $("<div class='discard_keyword glyphicon glyphicon-remove' data-value='keyword' title='Discard this keywors' onclick='discard_keyword(this)' style='color:red; cursor:pointer;'></div>");
    buttons.append(discard_button);
    buttons.append(add_button);
    new_keyword_element.append(buttons);

    var keyword_text= $("<p>"+keyword+"</p>");
    new_keyword_element.append(keyword_text);

    keyword_list.append(new_keyword_element)
};

function add_keyword(div){
    var keyword = $(div).parent().parent().find("p").text();
    var text_area = $("#keyword_text");
    text_area.append(keyword+", ");
    $(div).parent().parent().remove();
};

function discard_keyword(keyword){
    $(div).parent().parent().remove();
};
