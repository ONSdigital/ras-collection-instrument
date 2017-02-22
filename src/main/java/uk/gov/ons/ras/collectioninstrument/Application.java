package uk.gov.ons.ras.collectioninstrument;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.EnableAutoConfiguration;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;

@SpringBootApplication
@Configuration
@EnableAutoConfiguration
@ComponentScan(basePackages = {"uk.gov.ons.ras.collectioninstrument" })
public class Application {
  public static void main(String[] args) {
	 SpringApplication.run(Application.class, args);
  }
}