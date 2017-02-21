package uk.gov.ons.ras.collectioninstrument.jdbc;

import com.google.gson.Gson;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.core.RowMapper;

import javax.persistence.Transient;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.Map;

/**
 * Class for accessing the Collection Instrument table.
 *
 * We're using JDBC so that we can get access to the Json column type in Postgres,
 * which seems to be tricky and more complex to do through JPA.
 *
 */
public class CollectionInstrument {

    /**
     * Represents the Json stored in the content column.
     * As a convenience, this includes the database ID field when loaded.
     */
    public static class Json {
        @Transient
        public int id;
        public String urn;
        public String ciType;
        public String surveyId;
        public Map<String, String> classifiers;
    }

    static final String select = "select * from ras_collection_instruments where id=?";
    static final String insert = "insert into ras_collection_instruments (content) values (?)";

    /**
     * NB JdbcTemplate is thread-safe: http://stackoverflow.com/questions/467324/spring-jdbctemplate-and-threading
     */
    @Autowired
    JdbcTemplate jdbcTemplate;

    /**
     * Creates a new Collection Instrument record.
     * @param json The {@link Json} instance to be stored.
     */
    public void create(Json json) {
        jdbcTemplate.update(insert, new Gson().toJson(json));
    }

    /**
     * Reads collection instrument details for the given database row ID.
     * @param id The database row ID.
     * @return A {@link Json} instance representing the database row.
     */
    public Json read(int id) {
        return jdbcTemplate.queryForObject(
                select,
                new Object[]{id},
                new RowMapper<Json>() {
                    public Json mapRow(ResultSet rs, int rowNum) throws SQLException {
                        Json content = new Gson().fromJson(rs.getString("content"), Json.class);
                        content.id = rs.getInt("id");
                        return content;
                    }
                });
    }
}
