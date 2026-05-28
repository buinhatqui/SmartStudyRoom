package com.aiot.backend;

import org.springframework.boot.CommandLineRunner;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.Bean;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class BackendApplication {

	public static void main(String[] args) {
		System.out.println("\uD83E\uDEE6 SPRING_DATASOURCE_URL = " + System.getenv("SPRING_DATASOURCE_URL"));
		System.out.println("\uD83E\uDEE6 SPRING_DATASOURCE_USERNAME exists = " + (System.getenv("SPRING_DATASOURCE_USERNAME") != null));
		System.out.println("\uD83E\uDEE6 SPRING_DATASOURCE_PASSWORD exists = " + (System.getenv("SPRING_DATASOURCE_PASSWORD") != null));
		System.out.println("\uD83E\uDEE6 JWT_SIGNER_KEY exists = " + (System.getenv("JWT_SIGNER_KEY") != null));
		System.out.println("\uD83E\uDEE6 PORT = " + System.getenv("PORT"));

		SpringApplication.run(BackendApplication.class, args);
	}
}
