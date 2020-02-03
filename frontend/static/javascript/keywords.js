function fetch_suggested_keywords(value){
    $("#keyword_info").html("Loading suggested keywords...");
    $.getJSON("/author_keywords/" + value, {},
        function (data) {
            if (data.keywords != "" || data.keywords != null) {
                $.each(data.keywords, append_keywords); //ajax result contains a list of keywords (top 8 shown on website)
            };
            $("#keyword_info").html("");
        });
};

function show_keywords(){
    var keyword_list = $("#keywords");
    keyword_list.empty();
    for(var i=0; i<8; i++){
        if(suggested_keywords[i] == "" || suggested_keywords[i] == null){
            return null;
        }
        var new_keyword_element = $("<div class='keyword'></div>");
        var buttons = $("<div class='keyword_buttons'></div>");
        var add_button = $("<div class='add_keyword glyphicon glyphicon-ok' data-value='keyword' title='Add this keyword to list' onclick='add_keyword(this)' style='color:green; cursor:pointer;'></div>");
        var discard_button = $("<div class='discard_keyword glyphicon glyphicon-remove' data-value='keyword' title='Discard this keywors' onclick='discard_keyword(this)' style='color:red; cursor:pointer;'></div>");
        buttons.append(discard_button);
        buttons.append(add_button);
        new_keyword_element.append(buttons);

        var keyword_text= $("<p>"+suggested_keywords[i]+"</p>");
        new_keyword_element.append(keyword_text);

        keyword_list.append(new_keyword_element)
    };
};

function add_keyword(div){
    var keyword = $(div).parent().parent().find("p").text();
    var text_area = $("#keyword_text");
    if (!text_area.val()) {
        text_area.val(keyword);
    }else{
        new_text = text_area.val() + ", " + keyword;
        text_area.val(new_text);
    }
    $(div).parent().parent().remove();
    user_keywords.push(keyword);
    suggested_keywords = suggested_keywords.filter(function(e) { return e !== keyword })
    show_keywords();
};

function discard_keyword(div){
    var keyword = $(div).parent().parent().find("p").text();
    $(div).parent().parent().remove();
    suggested_keywords = suggested_keywords.filter(function(e) { return e !== keyword })
    show_keywords();
};

function append_keywords(index,keyword){
    if(suggested_keywords.includes(keyword) || user_keywords.includes(keyword)){
        return null;
    }
    suggested_keywords.push(keyword);
    show_keywords();
};