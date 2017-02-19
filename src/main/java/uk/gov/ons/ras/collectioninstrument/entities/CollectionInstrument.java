package uk.gov.ons.ras.collectioninstrument.entities;

import java.io.IOException;

import javax.persistence.Column;
import javax.persistence.Entity;
import javax.persistence.GeneratedValue;
import javax.persistence.GenerationType;
import javax.persistence.Id;
import javax.persistence.SequenceGenerator;
import javax.persistence.Table;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.ObjectWriter;

@Entity
@Table(schema = "collection_instrument",
	   name = "ras_collection_instruments")
public class CollectionInstrument {

    @Id
    @GeneratedValue(strategy = GenerationType.AUTO, generator = "G1")
    @SequenceGenerator(name = "G1", sequenceName = "collection_instrument.ras_collection_instruments_id_seq")
    @Column(name = "ID", nullable = false, unique = true)
    private Long id;
	
    /**
     * A string representation of the JSON content of this CollectionInstrument.
     */
	@Column(name = "CONTENT", nullable = false, unique = false)
    private String content;
	
    public Long getId() {
		return id;
	}

	public String getContent() {
		return content;
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
	
	public String getUrn() {	
		return getNode("id").asText();
	}

	public String getCiType() {	
		return getNode("ciType").asText();
	}

	public String getSurveyId() {	
		return getNode("surveyId").asText();
	}

	public String getClassifiers() {	
		return getNode("classifiers").asText();
	}
	
	/**
	 * Returns a child JSON node of this collection instrument's content JSON
	 * @param name
	 * @return The child JSON node requested
	 */
	private JsonNode getNode(String name) {	
		JsonNode contentJson = null;
		ObjectMapper mapper = new ObjectMapper();
        try {
			contentJson = mapper.readTree(content);
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		
		JsonNode node = contentJson.get(name);
		if (node != null)
		{
		    return node;
		}
		return contentJson;		
	}
	
    /**
     * Overridden toString to convert to a JSON formatted string.
     * @return this object as a string
     */
    @Override
    public final String toString() {
        String json = null;
        final ObjectWriter writer = new ObjectMapper()
                    .writer()
                    .withDefaultPrettyPrinter();
        try {
            json = writer.writeValueAsString(this);
        } catch (final JsonProcessingException e) {
           // LOGGER.error(e);
        }
        return json;
    }
}
