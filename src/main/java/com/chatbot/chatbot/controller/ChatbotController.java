package com.chatbot.chatbot.controller;

import java.util.HashMap;
import java.util.Map;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.HttpStatusCodeException;
import org.springframework.web.client.RestTemplate;

import com.chatbot.chatbot.service.DatabaseService;

@RestController
@RequestMapping("/chatbot")
@CrossOrigin("*")
public class ChatbotController {

    private static final Logger logger = LoggerFactory.getLogger(ChatbotController.class);

    @Autowired
    private DatabaseService databaseService;

    @PostMapping("/ask")
    public ResponseEntity<Map<String, String>> askQuestion(@RequestBody Map<String, String> payload) {
        String query = payload.get("query");

        logger.info("Received query: {}", query);

        RestTemplate restTemplate = new RestTemplate();
        String apiUrl = "http://localhost:5001/generate_sql";  // Python Flask API URL

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        Map<String, String> body = new HashMap<>();
        body.put("query", query);

        HttpEntity<Map<String, String>> entity = new HttpEntity<>(body, headers);
        logger.debug("Prepared request entity: {}", entity);

        ResponseEntity<Map> response;

        try {
            logger.debug("Sending request to Python Flask API.");
            response = restTemplate.postForEntity(apiUrl, entity, Map.class);
        } catch (HttpStatusCodeException e) {
            logger.error("HTTP error occurred while calling Python Flask API: {}", e.getResponseBodyAsString(), e);
            Map<String, String> errorResponse = new HashMap<>();
            errorResponse.put("response", "Python API error: " + e.getResponseBodyAsString());
            return ResponseEntity.status(e.getStatusCode()).body(errorResponse);
        } catch (Exception e) {
            logger.error("Unexpected error occurred while calling Python Flask API: {}", e.getMessage(), e);
            Map<String, String> errorResponse = new HashMap<>();
            errorResponse.put("response", "Unexpected error: " + e.getMessage());
            return ResponseEntity.status(500).body(errorResponse);
        }

        logger.debug("Response from Python Flask API: {}", response.getBody());

        String sqlQuery = null;
        if (response.getBody() != null && response.getBody().containsKey("sql_query")) {
            sqlQuery = (String) response.getBody().get("sql_query");
        } else {
            logger.error("Python Flask API response does not contain 'sql_query' field: {}", response.getBody());
            Map<String, String> errorResponse = new HashMap<>();
            errorResponse.put("response", "Invalid response from Python Flask API.");
            return ResponseEntity.status(500).body(errorResponse);
        }

        logger.info("Generated SQL Query: {}", sqlQuery);

        Map<String, String> responseMap = new HashMap<>();
        if (sqlQuery.toLowerCase().contains("select")) {
            logger.debug("Executing SQL query: {}", sqlQuery);
            try {
                String dbResponse = databaseService.executeSqlQuery(sqlQuery);
                logger.info("Database query executed successfully.");
                responseMap.put("response", dbResponse);
                return ResponseEntity.ok(responseMap);
            } catch (Exception e) {
                logger.error("Error executing SQL query: {}", e.getMessage(), e);
                responseMap.put("response", "Error executing query: " + e.getMessage());
                return ResponseEntity.status(500).body(responseMap);
            }
        }

        logger.warn("Generated SQL query is not valid. Returning response: {}", sqlQuery);
        responseMap.put("response", sqlQuery);
        return ResponseEntity.ok(responseMap);
    }
}
