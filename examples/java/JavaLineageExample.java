import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

public class JavaLineageExample {
    private static final String DEFAULT_MARQUEZ_URL = "http://localhost:5050";
    private static final String NAMESPACE = "java-example";
    private static final String JOB_NAME = "java-product-margin-pipeline";
    private static final String PRODUCER = "https://github.com/OpenLineage/OpenLineage/blob/v1-0-0/client";
    private static final String SCHEMA_URL = "https://openlineage.io/spec/1-0-5/OpenLineage.json#/definitions/RunEvent";

    public static void main(String[] args) throws Exception {
        String marquezUrl = System.getenv().getOrDefault("MARQUEZ_URL", DEFAULT_MARQUEZ_URL);
        String runId = UUID.randomUUID().toString();

        Path dataDir = Paths.get("..", "..", "data").normalize();
        Files.createDirectories(dataDir);

        Path inputPath = dataDir.resolve("products_java.csv");
        Path outputPath = dataDir.resolve("high_margin_products_java.csv");

        writeInputCsv(inputPath);

        String inputDataset = datasetJson(
            "products_java.csv",
            "file://" + inputPath.toAbsolutePath(),
            "[{\"name\":\"product_id\",\"type\":\"INTEGER\"},{\"name\":\"name\",\"type\":\"VARCHAR\"},{\"name\":\"cost\",\"type\":\"DOUBLE\"},{\"name\":\"price\",\"type\":\"DOUBLE\"},{\"name\":\"category\",\"type\":\"VARCHAR\"}]"
        );

        sendEvent(marquezUrl, eventJson("START", runId, "[" + inputDataset + "]", "[]"));

        List<String> outputRows = transform(inputPath);
        writeOutputCsv(outputPath, outputRows);

        String outputDataset = datasetJson(
            "high_margin_products_java.csv",
            "file://" + outputPath.toAbsolutePath(),
            "[{\"name\":\"product_id\",\"type\":\"INTEGER\"},{\"name\":\"name\",\"type\":\"VARCHAR\"},{\"name\":\"cost\",\"type\":\"DOUBLE\"},{\"name\":\"price\",\"type\":\"DOUBLE\"},{\"name\":\"margin\",\"type\":\"DOUBLE\"},{\"name\":\"category\",\"type\":\"VARCHAR\"}]"
        );

        sendEvent(marquezUrl, eventJson("COMPLETE", runId, "[" + inputDataset + "]", "[" + outputDataset + "]"));

        System.out.println("============================================================");
        System.out.println("Java Lineage Example Completed");
        System.out.println("============================================================");
        System.out.println("Run ID: " + runId);
        System.out.println("Input:  " + inputPath.toAbsolutePath());
        System.out.println("Output: " + outputPath.toAbsolutePath());
        System.out.println("Rows in output: " + outputRows.size());
        System.out.println("\nView in Marquez UI: http://localhost:3000");
        System.out.println("Search job: " + JOB_NAME);
        System.out.println("Namespace: " + NAMESPACE);
    }

    private static void writeInputCsv(Path inputPath) throws IOException {
        String csv = String.join("\n",
            "product_id,name,cost,price,category",
            "1,Laptop,850,1200,Electronics",
            "2,Mouse,12,25,Accessories",
            "3,Keyboard,40,75,Accessories",
            "4,Monitor,220,350,Electronics",
            "5,Headphones,90,150,Accessories",
            "6,Webcam,60,110,Electronics"
        ) + "\n";

        Files.writeString(inputPath, csv, StandardCharsets.UTF_8);
    }

    private static List<String> transform(Path inputPath) throws IOException {
        List<String> lines = Files.readAllLines(inputPath, StandardCharsets.UTF_8);
        List<String> outputRows = new ArrayList<>();

        for (int i = 1; i < lines.size(); i++) {
            String line = lines.get(i);
            if (line.trim().isEmpty()) {
                continue;
            }

            String[] parts = line.split(",");
            int productId = Integer.parseInt(parts[0]);
            String name = parts[1];
            double cost = Double.parseDouble(parts[2]);
            double price = Double.parseDouble(parts[3]);
            String category = parts[4];

            double margin = price - cost;
            if (margin >= 50.0) {
                outputRows.add(productId + "," + name + "," + cost + "," + price + "," + margin + "," + category);
            }
        }

        return outputRows;
    }

    private static void writeOutputCsv(Path outputPath, List<String> outputRows) throws IOException {
        List<String> lines = new ArrayList<>();
        lines.add("product_id,name,cost,price,margin,category");
        lines.addAll(outputRows);
        Files.write(outputPath, lines, StandardCharsets.UTF_8);
    }

    private static void sendEvent(String marquezUrl, String eventJson) throws IOException, InterruptedException {
        HttpClient client = HttpClient.newHttpClient();
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create(marquezUrl + "/api/v1/lineage"))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(eventJson))
            .build();

        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
        int status = response.statusCode();

        if (status < 200 || status >= 300) {
            throw new RuntimeException("Failed to send lineage event. HTTP " + status + " Body: " + response.body());
        }
    }

    private static String eventJson(String eventType, String runId, String inputsJson, String outputsJson) {
        return "{" +
            "\"eventType\":\"" + eventType + "\"," +
            "\"eventTime\":\"" + Instant.now().toString() + "\"," +
            "\"run\":{\"runId\":\"" + runId + "\"}," +
            "\"job\":{\"namespace\":\"" + NAMESPACE + "\",\"name\":\"" + JOB_NAME + "\"}," +
            "\"inputs\":" + inputsJson + "," +
            "\"outputs\":" + outputsJson + "," +
            "\"producer\":\"" + PRODUCER + "\"," +
            "\"schemaURL\":\"" + SCHEMA_URL + "\"" +
            "}";
    }

    private static String datasetJson(String name, String uri, String fieldsJson) {
        return "{" +
            "\"namespace\":\"" + NAMESPACE + "\"," +
            "\"name\":\"" + name + "\"," +
            "\"facets\":{" +
                "\"schema\":{" +
                    "\"_producer\":\"" + PRODUCER + "\"," +
                    "\"_schemaURL\":\"https://openlineage.io/spec/facets/1-0-0/SchemaDatasetFacet.json\"," +
                    "\"fields\":" + fieldsJson +
                "}," +
                "\"dataSource\":{" +
                    "\"_producer\":\"" + PRODUCER + "\"," +
                    "\"_schemaURL\":\"https://openlineage.io/spec/facets/1-0-0/DatasourceDatasetFacet.json\"," +
                    "\"name\":\"file\"," +
                    "\"uri\":\"" + uri + "\"" +
                "}" +
            "}" +
            "}";
    }
}
