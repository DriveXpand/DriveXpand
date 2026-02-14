package com.tools;

import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

public class PasswordGenerator {

    public static void main(String[] args) {
        // Default to "test" if no argument provided
        String rawPassword = (args.length > 0) ? args[0] : "test";

        BCryptPasswordEncoder encoder = new BCryptPasswordEncoder();
        String hash = encoder.encode(rawPassword);

        System.out.println("\n========================================================");
        System.out.println(" PASSWORD: " + rawPassword);
        System.out.println("========================================================\n");

        System.out.println("1. FOR DATABASE (Raw Hash):");
        System.out.println(hash);
        System.out.println();

        System.out.println("2. FOR APPLICATION.PROPERTIES (Spring Boot):");
        System.out.println("{bcrypt}" + hash);
        System.out.println();

        System.out.println("3. FOR DOCKER COMPOSE (Escaped $$):");
        // We replace every single '$' with '$$' so Docker doesn't break it
        String dockerHash = "{bcrypt}" + hash.replace("$", "$$");
        System.out.println(dockerHash);

        System.out.println("\n========================================================");
    }
}
