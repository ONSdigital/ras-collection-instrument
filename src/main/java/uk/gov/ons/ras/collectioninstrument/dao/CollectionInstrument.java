package uk.gov.ons.ras.collectioninstrument.dao;

import com.google.gson.annotations.SerializedName;

import javax.persistence.Transient;
import java.util.Map;

/**
 * Represents the Json stored in the content column in the database.
 */
public class CollectionInstrument {
    public String reference;
    public String urn;
    public String ciType;
    public String surveyId;
    public Map<String, String> classifiers;

    @SerializedName("$schema")
    public String schema = "/schema/collectioninstrument";
}
