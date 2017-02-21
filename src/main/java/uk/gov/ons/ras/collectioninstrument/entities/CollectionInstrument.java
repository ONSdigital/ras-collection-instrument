package uk.gov.ons.ras.collectioninstrument.entities;

import com.google.gson.Gson;
import com.google.gson.GsonBuilder;

import javax.persistence.*;
import java.util.Map;

@Entity
@Table(schema = "ras_collection_instrument",
        name = "ras_collection_instruments")
public class CollectionInstrument {

    public static class Json {
        public String urn;
        public String ciType;
        public String surveyId;
        public Map<String, String> classifiers;
    }

    /**
     * Default constructor.
     */
    public CollectionInstrument() {
        // Default constructor
    }

    /**
     * Use this constructor when creating a new collection instrument.
     *
     * @param json The Json data to be saved.
     */
    public CollectionInstrument(Json json) {
        content = new Gson().toJson(json);
    }

    /**
     * The primary key for this CollectionInstrument.
     */
    @Id
    @GeneratedValue(strategy = GenerationType.AUTO, generator = "G1")
    @SequenceGenerator(name = "G1", sequenceName = "ras_collection_instrument.ras_collection_instruments_id_seq")
    @Column(name = "ID", nullable = false, unique = true)
    private Long id;

    /**
     * A string representation of the JSON content of this CollectionInstrument.
     */
    @Column(name = "CONTENT", nullable = false, unique = false)
    private String content;

    /**
     * {@link Json} object Parsed from {@link #content} field.
     */
    private Json json;

    public Long getId() {
        return id;
    }

    public String getContent() {
        return content;
    }

    public Json getJson() {
        return parse();
    }

	/* Once content is assigned we can pull out the individual fields from the content e.g
    {id: 2,
	 content: {
		"id": "urn:ons.gov.uk:id:ci:001.001.00002",
		"ciType": "OFFLINE",
		"surveyId": "urn:ons.gov.uk:id:survey:001.001.00002",
		"classifiers": {"RU_REF": "01234567890"}
		}
	}
	
	*/

    /**
     * urn of the CollectionInstrument.
     *
     * @return
     */
    public String getUrn() {
        return parse().urn;
    }

    /**
     * Type of CollectionInstrument.
     *
     * @return
     */
    public String getCiType() {
        return parse().ciType;

    }

    /**
     * Survey ID of this CollectionInstrument.
     *
     * @return
     */
    public String getSurveyId() {
        return parse().surveyId;
    }

    /**
     * The array of Classifiers and their values for this CollectionInstrument.
     *
     * @return
     */
    public Map<String, String> getClassifiers() {
        return parse().classifiers;
    }

    /**
     * Parses the content to a Json structure.
     */
    private Json parse() {
        if (json == null) {
            json = new Gson().fromJson(content, Json.class);
        }
        return json;
    }

    /**
     * Overridden toString to convert to a JSON formatted string.
     *
     * @return this object as a string
     */
    @Override
    public final String toString() {
        // Use pretty printing
        Gson gson = new GsonBuilder().setPrettyPrinting().create();
        return gson.toJson(content);
    }

}
