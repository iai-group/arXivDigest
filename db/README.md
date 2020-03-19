# Database Back-end

| Tables | Fields |
| ------------- | ------------- |
| users | user_id, email, salted_hash, firstname, lastname, notification_interval, last_recommendation_date, last_email_date, registered, admin, organization, dblp_profile, google_scholar_profile, semantic_scholar_profile, personal_website|
| user_categories | user_id, category_id |
| user_topics | user_id, topic_id, state |
| topics | topic_id, topic, filtered |
| articles | article_id, title, abstract, doi, comments, licence, journal, datestamp |
| article_authors | author_id, article_id, firstname, lastname |
| article_categories | article_id, category_id |
| author_affiliations | author_id, affiliation |
| categories | category_id, category, subcategory, category_name |
| article_recommendations | user_id, article_id, system_id, score, recommendation_date, explanation |
| systems | system_id, api_key, system_name, active, admin_user_id |
| article_feedback | user_id, article_id, system_id, score, recommendation_date, seen_email, seen_web, clicked_email, clicked_web, saved, trace_save_email, trace_click_email, explanation |
| feedback | feedback_id, user_id, article_id, type, feedback_text |
| topic_recommendations | recommendation_id, user_id, topic_id, system_id, datestamp, system_score, interleaving_order, seen, clicked |
| database_version | current_version |