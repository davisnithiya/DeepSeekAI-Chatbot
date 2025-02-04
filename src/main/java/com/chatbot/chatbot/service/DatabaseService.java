package com.chatbot.chatbot.service;

import java.util.List;
import java.util.Map;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.stereotype.Service;

@Service
public class DatabaseService {

	@Autowired
	private JdbcTemplate jdbcTemplate;

	public String executeSqlQuery(String query) {
		// Example method to execute query and return results as a formatted string
		List<Map<String, Object>> results = jdbcTemplate.queryForList(query);

		// Convert the results to a string format (e.g., JSON or simple string)
		StringBuilder resultString = new StringBuilder();

		for (Map<String, Object> row : results) {
			for (Map.Entry<String, Object> entry : row.entrySet()) {
				resultString.append(entry.getKey() + ": " + entry.getValue() + ", ");
			}
			resultString.append("\n");
		}

		return resultString.toString().isEmpty() ? "No results found" : resultString.toString();
	}
}
