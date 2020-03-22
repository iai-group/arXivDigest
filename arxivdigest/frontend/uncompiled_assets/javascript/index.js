$(document).ready(function () {
    if (top.location.pathname === '/'){
        show_topics(); 
    }    
});

function show_topics(){
    var topic_list = $("#index_topic_list");
    topic_list.empty();
    var title = $("<li class='list-group-item'><h4 style='text-align: center;'>Suggested Topics:</h4></li>");
    topic_list.append(title);
    for (var i = 0; i < 8; i++){
        if (suggested_topics[i] == null){
            var end = $("<li class='list-group-item topic-end'><h5>-No more suggested topics at the moment-</h5></li>")
            topic_list.append(end);
            return null
        }
        var new_topic_element = $("<li class='list-group-item'></li>");
        var ok_button = $(`<div class='glyphicon glyphicon-ok alignright topic-symbol' title='Add this topic to your profile'
                          data-value=`+ suggested_topics[i]['topic_id']+` onclick='add_topic(this)' style='color:rgb(103, 134, 103); padding-right:20px;'></div>`);
        var remove_button = $(`<div class='glyphicon glyphicon-remove alignright topic-symbol' title='Remove this topic suggestion'
                          data-value=`+ suggested_topics[i]['topic_id']+` onclick='reject_topic(this)' style='color:rgb(177, 119, 119);'></div>`);
        var topic_text = $("<p>"+suggested_topics[i]['topic']+"</p>");
        new_topic_element.append(ok_button);
        new_topic_element.append(remove_button);
        new_topic_element.append(topic_text);
        topic_list.append(new_topic_element);            
    }
}

function add_topic(div){
    var topic_id = $(div).data()['value'];
    $("#topic_error").html('')
    
    $.getJSON("/update_topic/"+topic_id+"/SYSTEM_RECOMMENDED_ACCEPTED",{},
        function(data){
            if (data.result == "success"){
                remove_topic(topic_id);
            }
            if (data.result == "fail"){
                $("#topic_error").html("Failed to add topic, try again later.");
            }
        });
}

function reject_topic(div){
    var topic_id = $(div).data()['value'];
    $("#topic_error").html('')
    
    $.getJSON("/update_topic/"+topic_id+"/SYSTEM_RECOMMENDED_REJECTED",{},
        function(data){
            if (data.result == "success"){
                remove_topic(topic_id);
            }
            if (data.result == "fail"){
                $("#topic_error").html("Failed to reject topic, try again later.");
            }
        });
}

function remove_topic(topic_id){
    suggested_topics = suggested_topics.filter(function (e){
        return e['topic_id'] !== topic_id;
    });
    show_topics();
}